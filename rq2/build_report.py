"""Sinh toàn bộ báo cáo, gồm văn xuôi có truy vết và các bảng từ CSV."""
import re
from pathlib import Path
from statistics import mean

from rq2.analyze_rq2 import (CODECS, STATES, fmt, read_rows, summarize,
                             table_markdown, write_unchanged_or_new)

TRACE_COLUMNS = ("ID", "Nhận định", "file/codec/state", "Nguồn", "Phép tính", "Giá trị")


def build_report(csv_path, out_dir, report_path, mechanism_path, overwrite=False):
    rows = read_rows(csv_path)
    ratios, speeds = summarize(rows)
    lookup = {(r['file'], r['codec'], r['state']): r for r in ratios}
    files = sorted({r['file'] for r in rows})
    mechanism = mechanism_path.read_text(encoding='utf-8').splitlines()
    traces = []

    def trace(label, scope, source, operation, value):
        ident = f"T{len(traces)+1:03d}"
        traces.append(dict(zip(TRACE_COLUMNS, (ident, label, scope, source, operation, value))))
        return f"**{value}** [{ident}]"

    def csv_value(file, codec, state, metric='ratio', aggregate='mean', label=None):
        selected = [(i, r) for i, r in enumerate(rows, 2)
                    if (file is None or r['file'] == file)
                    and (codec is None or r['codec'] == codec)
                    and (state is None or r['state'] == state)]
        def get(row):
            if metric == 'ratio-h0_ratio':
                return float(row['ratio']) - float(row['h0_ratio'])
            if metric == 'ratio_no_header':
                return float(row['notes'].split('=')[1])
            return float(row[metric])
        value = {'mean': mean, 'min': min, 'max': max}[aggregate]([get(r) for _, r in selected])
        display = str(int(value)) if metric in ('orig_bytes', 'comp_bytes') else fmt(value)
        return trace(label or metric, '/'.join((file or '*', codec or '*', state or '*')),
                     'CSV:' + ','.join(str(i) for i, _ in selected), f'{aggregate}({metric})', display)

    def mech_value(file, contains, pattern, label):
        start = next((i for i, line in enumerate(mechanism) if line.startswith('== ' + file)), 0) if file else 0
        index = next(i for i in range(start, len(mechanism)) if contains in mechanism[i])
        match = re.search(pattern, mechanism[index])
        if not match:
            raise ValueError((contains, pattern))
        begin, end = match.span(1)
        return trace(label, (file or 'thiết lập') + '/script', f'MECH:{index+1}',
                     f'slice({begin},{end})', match.group(1))

    def block(name, text):
        return f'<!-- BEGIN:{name} -->\n{text.rstrip()}\n<!-- END:{name} -->'

    p = ['# RQ2 — Ảnh hưởng của thứ tự byte đến hiệu quả nén',
         'Bản sinh tự động bằng `python -m rq2.analyze_rq2 --overwrite --report rq2/RQ2_report_draft.md`. '
         'Nguồn duy nhất của kết quả thực nghiệm là `results_rq2_all.csv`; kiểm chứng cơ chế lấy từ '
         '`out/mechanism_output.txt`. Không đo lại benchmark. Các mã T ở văn xuôi liên kết tới bảng truy vết cuối báo cáo.',
         '## 1. Mục đích và thiết lập']
    p.append('[ĐO ĐƯỢC] Khảo sát ' + mech_value(None, 'CSV:', r'; (\d+) file', 'Số file') +
             ' file, ' + mech_value(None, 'CSV:', r'; (\d+) state', 'Số state') + ' state (original, runs, shuffled), ' +
             mech_value(None, 'CSV:', r'; (\d+) codec', 'Số codec') + ' codec (Huffman, RLE, LZW). Seeds là ' +
             mech_value(None, 'CSV:', r'seeds = (\[.*\])', 'Danh sách seed') + '; đo ' +
             mech_value(None, 'repeats =', r'repeats = (\d+)', 'Số lần đo theo log') +
             ' lần lấy trung vị thời gian. Số lần đo lấy từ log cũ được script in lại, không suy ra từ CSV; nhóm còn phải xác nhận thiết lập này.')
    p.append('[ĐO ĐƯỢC] CSV có ' + mech_value(None, 'CSV:', r'CSV: (\d+) dong', 'Số dòng CSV') +
             ' dòng, ' + mech_value(None, 'CSV:', r'; (\d+) cot', 'Số cột CSV') +
             ' cột. Tỷ lệ = comp_bytes/orig_bytes, gồm header. Huffman còn ghi ratio_no_header, loại ' +
             mech_value(None, 'Hang so', r'header = (\d+) byte', 'Header Huffman') +
             ' byte; bảng lấy trực tiếp từ notes của CSV, validator đối chiếu thêm bằng số byte. '
             'H0/8 là entropy biên của byte quy về byte/byte. State runs sắp xếp byte tăng dần; shuffled hoán vị byte giữ histogram. '
             'Mỗi dòng shuffled ở bảng là trung bình các seed, ratio_min/max giữ khoảng dao động giữa seed. '
             'Thông lượng được trung bình từ các giá trị đã ghi trong CSV; không tính ngược từ thời gian trung bình. '
             'Đỉnh bộ nhớ đo ở một lượt tracing riêng theo runner hiện có.')
    descriptions = ['văn bản tiếng Anh', 'dữ liệu nhị phân', 'văn bản tiếng Việt UTF-8']
    for file, description in zip(files, descriptions):
        p.append(f'[ĐO ĐƯỢC] `{file}` ({description}) có ' + csv_value(file, 'huffman', 'original', 'orig_bytes', label='Kích thước file') + ' byte.')
    p += ['## 2. Kết quả',
          '[ĐO ĐƯỢC] Các bảng dưới được sinh từ CSV. Cột “tốt hơn mốc H0/8?” có nghĩa ratio < h0_ratio; '
          'đây là so sánh kích thước, không phải kiểm định ý nghĩa thống kê. Bảng tốc độ giữ dữ liệu alice để tra cứu; '
          'chỉ so sánh tốc độ kennedy và V1 ở phần phân tích.',
          block('ratio', (out_dir / 'rq2_table_ratio.md').read_text(encoding='utf-8')),
          block('speed', (out_dir / 'rq2_table_speed.md').read_text(encoding='utf-8')),
          block('comparison', (out_dir / 'rq2_table_comparison.md').read_text(encoding='utf-8')),
          '![Tỷ lệ nén, trục log, đường H0/8 và hoa văn đen trắng](out/rq2_ratio.png)',
          '![Thông lượng nén trên các file lớn](out/rq2_speed.png)',
          '## 3. Phân tích từng codec', '### Huffman']
    for file in files:
        p.append(f'[ĐO ĐƯỢC] `{file}`/huffman ở original, runs và từng seed shuffled đều có comp_bytes = ' +
                 csv_value(file, 'huffman', None, 'comp_bytes', label='Kích thước Huffman bất biến (validator kiểm tra từng dòng)') +
                 ' byte; ratio = ' + csv_value(file, 'huffman', 'original') +
                 '; ratio không header = ' + csv_value(file, 'huffman', 'original', 'ratio_no_header') + '.')
    p.append('[GIẢI THÍCH - cần kiểm chứng] Lý thuyết mã tĩnh bậc không: H0 chỉ phụ thuộc histogram; '
             'hoán vị byte giữ histogram nên giữ H0. Huffman tĩnh xây độ dài mã từ histogram, do đó tổng số bit mã, '
             'padding và header cố định giữ nguyên kích thước. Đây là lập luận lý thuyết; sự bất biến trên các file ở trên là phần đo được, '
             'không khẳng định mọi blob nén giống nhau hay mọi cách cài đặt Huffman đều có cùng overhead.')
    p.append('### RLE')
    for file in files:
        p.append(f'[ĐO ĐƯỢC] `{file}`/rle: original = ' + csv_value(file, 'rle', 'original') +
                 ', runs = ' + csv_value(file, 'rle', 'runs') + ', shuffled = ' + csv_value(file, 'rle', 'shuffled') +
                 '. Runs nén mạnh; original và shuffled đều phình so với dữ liệu đầu vào.')
    p.append('[GIẢI THÍCH - cần kiểm chứng] Gom các byte bằng nhau tạo run dài và giảm số cặp đếm/byte. '
             'Giới hạn count là ' + mech_value(None, 'Hang so', r'toi da = (\d+)', 'Giới hạn count RLE') +
             ', header RLE là ' + mech_value(None, 'Hang so', r'RLE header = (\d+)', 'Header RLE') +
             ' byte; validator kiểm tra kích thước runs bằng header cộng số byte của các cặp sau tách run. '
             'Đây là công thức của định dạng; không phải giả định rằng chỉ cần một cặp cho mỗi giá trị byte.')
    p.append('### LZW và phân tích theo file')
    for file, desc in zip(files, descriptions):
        p.append(f'[ĐO ĐƯỢC] `{file}` ({desc})/lzw: original = ' + csv_value(file, 'lzw', 'original') +
                 ', runs = ' + csv_value(file, 'lzw', 'runs') + ', shuffled trung bình = ' + csv_value(file, 'lzw', 'shuffled') +
                 ', shuffled nhỏ nhất = ' + csv_value(file, 'lzw', 'shuffled', aggregate='min') +
                 '. Mọi seed shuffled đều kém original. ' +
                 ('Gom run cải thiện LZW; RLE-runs vẫn nhỏ hơn. ' if file != files[-1] else
                  'Gom run làm LZW phình; RLE-runs vẫn nhỏ hơn rất nhiều. ') +
                 'Ở original, LZW có tỷ lệ thấp nhất trong các codec; ở shuffled, Huffman thấp nhất (xem bảng cùng state).')
    p.append('### Tốc độ và bộ nhớ')
    p.append('[ĐO ĐƯỢC] Chỉ so sánh tốc độ trên kennedy.xls và v1_test_1mib.txt. '
             'alice29.txt nhỏ hơn đáng kể; riêng thời gian nén huffman/original là ' +
             csv_value(files[0], 'huffman', 'original', 'comp_ms', label='Thời gian alice, chỉ để nêu hạn chế') +
             ' ms. [GIẢI THÍCH - cần kiểm chứng] Khoảng thời gian ngắn dễ bị ảnh hưởng bởi scheduling và nhiễu hệ thống; '
             'CSV không giữ các lần lặp riêng nên chưa định lượng được mức nhiễu.')
    for file in files[1:]:
        p.append(f'[ĐO ĐƯỢC] `{file}`/original: tốc độ nén huffman/rle/lzw lần lượt là ' +
                 ', '.join(csv_value(file, c, 'original', 'comp_kibs', label='Tốc độ nén original') for c in CODECS) +
                 ' KiB/s; giải nén lần lượt là ' +
                 ', '.join(csv_value(file, c, 'original', 'decomp_kibs', label='Tốc độ giải nén original') for c in CODECS) +
                 ' KiB/s. RLE/runs đạt ' + csv_value(file, 'rle', 'runs', 'comp_kibs', label='Tốc độ nén RLE-runs') +
                 ' KiB/s, cao hơn RLE/original trong phép đo này. Bộ nhớ đỉnh huffman/rle/lzw ở original lần lượt là ' +
                 ', '.join(csv_value(file, c, 'original', 'peak_mem_kib', label='Bộ nhớ đỉnh original') for c in CODECS) + ' KiB.')
    p.append('[ĐO ĐƯỢC] Bảng cho thấy bộ nhớ đỉnh Huffman cao hơn RLE và LZW ở mọi file/state. '
             '[GIẢI THÍCH - cần kiểm chứng] Mã Huffman hiện có tạo chuỗi ký tự bit trong Python khi nén và giải nén; '
             'điều này phù hợp với mức bộ nhớ cao. Đây là đặc điểm cài đặt, không phải bản chất bắt buộc của thuật toán Huffman; '
             'chưa đo một cài đặt khác để tách riêng đóng góp của chuỗi bit.')
    p.append('## 4. So với mốc H0/8')
    p.append('[ĐO ĐƯỢC] Huffman có ratio cao hơn H0/8 từ ' +
             csv_value(None, 'huffman', None, 'ratio-h0_ratio', 'min', 'Chênh lệch Huffman–H0 nhỏ nhất') + ' đến ' +
             csv_value(None, 'huffman', None, 'ratio-h0_ratio', 'max', 'Chênh lệch Huffman–H0 lớn nhất') +
             '. Giữ cùng quy tắc định dạng với bảng; không thay bằng khoảng xấp xỉ khác.')
    for file in files:
        p.append(f'[ĐO ĐƯỢC] `{file}`: lzw/original = ' + csv_value(file, 'lzw', 'original') +
                 ' < H0/8 = ' + csv_value(file, 'huffman', 'original', 'h0_ratio') +
                 '; Huffman bỏ header vẫn = ' + csv_value(file, 'huffman', 'original', 'ratio_no_header') +
                 ' > H0/8. Khi shuffled, LZW = ' + csv_value(file, 'lzw', 'shuffled') +
                 ' > Huffman = ' + csv_value(file, 'huffman', 'shuffled') + '. Kết quả đúng cả với alice, không chỉ kennedy và V1.')
    p.append('[GIẢI THÍCH - cần kiểm chứng] H0/8 không phải cận dưới cho codec dựa trên ngữ cảnh. '
             'Entropy biên bỏ qua phụ thuộc giữa các byte; mã chuỗi có thể khai thác các cụm lặp để xuống dưới mốc này. '
             'Xáo trộn phá cấu trúc chuỗi trong khi giữ histogram, phù hợp với việc LZW mất lợi thế; '
             'không diễn giải thành vi phạm giới hạn entropy của nguồn có ngữ cảnh.')
    p.append('## 5. Giả thuyết và kết quả')
    verdicts = []
    huffman_ok = all(len({r['comp_bytes'] for r in rows if r['file'] == f and r['codec'] == 'huffman'}) == 1 for f in files)
    huffman_ok &= all(r['ratio'] >= r['h0_ratio'] and r['ratio_no_header'] > r['h0_ratio'] for r in ratios if r['codec'] == 'huffman')
    rle_ok = all(lookup[f, 'rle', 'runs']['ratio'] < 1 and lookup[f, 'rle', 'original']['ratio'] > 1
                 and lookup[f, 'rle', 'shuffled']['ratio_min'] > 1 for f in files)
    lzw_ok = all(lookup[f, 'lzw', 'shuffled']['ratio_min'] > lookup[f, 'lzw', 'original']['ratio'] for f in files)
    for title, ok, evidence in [
        ('Huffman bất biến và không thấp hơn H0/8, kể cả bỏ header', huffman_ok, 'comp_bytes và ratio_no_header: phần Huffman; chênh lệch H0: phần so mốc'),
        ('RLE tốt sau gom run, phình ở original/shuffled', rle_ok, 'ratio và ratio_min: bảng tỷ lệ và phần RLE'),
        ('LZW tệ đi sau xáo trộn ở từng file, từng seed', lzw_ok, 'ratio_min shuffled lớn hơn original: phần LZW')]:
        verdicts.append({'Giả thuyết': title, 'Verdict': 'ĐÚNG' if ok else 'SAI', 'Căn cứ [ĐO ĐƯỢC]': evidence})
    improved = [f for f in files if lookup[f, 'lzw', 'runs']['ratio'] < lookup[f, 'lzw', 'original']['ratio']]
    verdicts.append({'Giả thuyết': 'Gom run luôn cải thiện LZW',
                     'Verdict': 'ĐÚNG' if len(improved) == len(files) else ('ĐÚNG MỘT PHẦN; mệnh đề luôn là SAI' if improved else 'SAI'),
                     'Căn cứ [ĐO ĐƯỢC]': 'Cải thiện: ' + ', '.join(improved) + '; còn lại: ' + ', '.join(f for f in files if f not in improved)})
    p.append(block('hypotheses', table_markdown(verdicts, ('Giả thuyết', 'Verdict', 'Căn cứ [ĐO ĐƯỢC]'))))
    p += ['## 6. Thảo luận cơ chế', '### Bất thường: LZW-runs trên V1 phình, alice rất thấp']
    for file in files:
        line = next(s for i, s in enumerate(mechanism) if "LZW 'runs':" in s and
                    any(x.startswith('== ' + file) for x in mechanism[max(0, i-3):i]))
        p.append(f'[ĐO ĐƯỢC] `{file}`/lzw: runs = ' + csv_value(file, 'lzw', 'runs') +
                 ', original = ' + csv_value(file, 'lzw', 'original') + '; chênh lệch runs − original = ' +
                 mech_value(file, "LZW 'runs':", r'delta ratio = ([-\d.e+]+)', 'Chênh lệch LZW runs-original') + '. ' +
                 ('Từ điển runs không đầy.' if 'KHONG day' in line else
                  'Từ điển runs đầy tại chỉ số byte ' + mech_value(file, "LZW 'runs':", r'tai byte (\d+)', 'Vị trí đầy từ điển runs') +
                  ', tương ứng ' + mech_value(file, "LZW 'runs':", r'\((\d+)%', 'Phần trăm vị trí đầy, định dạng script') +
                  '% dữ liệu; phần sau dùng từ điển đóng băng là ' + mech_value(file, "LZW 'runs':", r'; (\d+)%', 'Phần trăm sau khi đầy') + '% (tỷ lệ phần trăm đã làm tròn theo script).'))
    p.append('[ĐO ĐƯỢC] Script xác nhận từ điển giới hạn ' + mech_value(None, 'Hang so', r'LZW = (\d+)', 'Dung lượng từ điển LZW') +
             ' mục đầy sớm hơn trên V1-runs so với kennedy-runs; alice-runs không đầy. '
             '[GIẢI THÍCH - cần kiểm chứng] Khi duyệt dữ liệu đã sắp xếp, các mục từ điển có thể được dùng hết cho những giá trị byte xuất hiện trước, '
             'khiến các giá trị xuất hiện sau không được học cụm mới. Kết quả thời điểm đầy phù hợp với cơ chế này. '
             'Chỉ số đầy không dự đoán một tỷ lệ nén cụ thể: chưa có phép đo đối chứng thay chính sách từ điển, '
             'nên chưa xác nhận nguyên nhân đầy đủ hay độ lớn của mức phình. Không kết luận chỉ số lượng giá trị byte quyết định kết quả: '
             'kennedy có nhiều giá trị byte hơn V1 nhưng đầy muộn hơn. LZW-original cũng đầy theo output script; đầy từ điển tự nó không đủ giải thích.')
    p.append('### Bất thường: RLE-original của kennedy tệ hơn shuffled')
    for file in files:
        p.append(f'[ĐO ĐƯỢC] `{file}`/rle: sum(p²) = ' + mech_value(file, 'sum(p^2)', r'sum\(p\^2\) = ([\d.]+)', 'Tổng bình phương xác suất byte') +
                 '; dự đoán shuffled = ' + mech_value(file, 'sum(p^2)', r'\) = ([\d.]+); CSV', 'Dự đoán RLE shuffled') +
                 ', CSV = ' + csv_value(file, 'rle', 'shuffled') + ', chênh lệch CSV − dự đoán = ' +
                 mech_value(file, 'sum(p^2)', r'delta = ([-\d.e+]+)', 'Sai lệch dự đoán RLE shuffled') +
                 '; dự đoán original = ' + mech_value(file, 'so run', r'run/n = ([\d.]+)', 'Dự đoán RLE original') +
                 ', CSV = ' + csv_value(file, 'rle', 'original') + ', chênh lệch = ' +
                 mech_value(file, 'so run', r'delta = ([-\d.e+]+)', 'Sai lệch dự đoán RLE original') + '. ' +
                 'Kết luận đối chiếu trong script: ' +
                 ('KHỚP.' if all('KHOP' in mechanism[next(i for i, s in enumerate(mechanism) if s.startswith('== ' + file)) + offset]
                                for offset in (1, 2)) else 'LỆCH; xem output.'))
    p.append('[ĐO ĐƯỢC] Sai số tuyệt đối của các dự đoán RLE đều nhỏ hơn ngưỡng đối chiếu ' +
             mech_value(None, 'Quy uoc:', r'< ([\d.]+)', 'Ngưỡng đối chiếu RLE') +
             '. Sai lệch được tính trước khi định dạng số nên có thể khác phép trừ trực tiếp hai số đã làm tròn. '
             'Riêng kennedy, cả dự đoán và CSV đều cho shuffled thấp hơn original. '
             '[GIẢI THÍCH - cần kiểm chứng] Với hoán vị ngẫu nhiên, xác suất byte kề nhau bằng nhau gần sum(p²), '
             'nên tỷ lệ RLE gần hai lần xác suất đổi byte. Công thức kỳ vọng bỏ qua header, tách run dài và hiệu chỉnh lấy mẫu không hoàn lại; '
             'đối chiếu hiện tại ủng hộ cơ chế này cho kennedy, không xác nhận mọi hoán vị đều có cùng kết quả. '
             'Phân tích theo số run gốc giải thích được vì sao một file nhị phân vẫn có thể nhiều chuyển byte hơn bản xáo trộn.')
    p += ['## 7. Hạn chế',
          '- [ĐO ĐƯỢC] `tracemalloc` theo dõi bộ nhớ do Python cấp phát trong lượt nén và giải nén riêng, không đo toàn bộ RSS hoặc mọi cấp phát native. '
          'CSV chỉ lưu giá trị tổng hợp; không còn phân bố từng lần đo để tính độ không chắc chắn.',
          '- [ĐO ĐƯỢC] Chỉ dùng các seed và số lần đo nêu ở phần thiết lập trên một máy; chưa kiểm chứng tính tái lập trên máy khác. '
          'Seed và số lần đo vẫn chờ nhóm xác nhận. Chỉ so sánh tốc độ trên kennedy và V1.',
          '- [GIẢI THÍCH - cần kiểm chứng] Header Huffman cố định ảnh hưởng tỷ lệ ở file nhỏ mạnh hơn. '
          'V1 được Cặp 1 chuẩn bị bằng cách cắt tại ranh giới ký tự UTF-8 nên về quy trình có thể ngắn hơn danh nghĩa vài byte; '
          'file hiện tại có đúng kích thước ghi ở phần thiết lập, không quan sát thấy thiếu byte danh nghĩa trong bản này.',
          '- [ĐO ĐƯỢC] LZW đóng băng từ điển theo yêu cầu đề; không thay bằng reset hay tăng kích thước. '
          'Việc kiểm tra thời điểm đầy chưa phải phép kiểm định nhân quả.',
          '- Schema CSV của Cặp 1 và nhóm 2 có cùng số cột nêu ở thiết lập nhưng khác API: Cặp 1 dùng `CsvWriter`, '
          '`h0_bits`, `throughput_kibs`; nhóm 2 dùng `append_row`, `finalize_row`, `validate_row`, `sha16`. '
          '`common/csv_schema.md` vẫn là đề xuất chờ nhóm chốt; chưa thay schema hay sửa code Cặp 1.',
          '- Hash rút gọn trong CSV được đối chiếu với file gốc cho state original; không chạy lại giải nén trong lượt phân tích này. '
          'Validator dùng cờ round-trip và log của lượt đo trước. Không diễn giải thành tái đo toàn bộ phép thử.',
          '- Không thêm tài liệu tham khảo chưa kiểm chứng; bản này chưa trích dẫn tài liệu ngoài. '
          'Khi ghép báo cáo chung chỉ dùng các tài liệu bắt buộc của đề đã được nhóm đối chiếu.',
          '## 8. Kết luận',
          '[ĐO ĐƯỢC] Trên bộ dữ liệu đã đo, Huffman giữ kích thước theo thứ tự byte; RLE hưởng lợi mạnh từ gom run; '
          'LZW kém đi sau xáo trộn và không luôn tốt lên sau gom run. LZW-original xuống dưới mốc H0/8 trên mọi file, '
          'nhưng Huffman có tỷ lệ tốt nhất ở shuffled. Kết quả cơ chế RLE khớp gần đúng; cơ chế từ điển LZW được hỗ trợ '
          'bởi thời điểm đầy, còn quan hệ nhân quả cần đối chứng. Những kết quả này chỉ mô tả bộ dữ liệu và cài đặt đã đo.',
          '## Truy vết số liệu',
          'Mỗi giá trị định lượng trích ở văn xuôi có mã T. CSV đánh số dòng vật lý, header là dòng đầu; '
          'MECH đánh số dòng trong `out/mechanism_output.txt`. `mean`, `min`, `max` áp dụng lên các dòng liệt kê; '
          '`ratio-h0_ratio` tính trước khi tổng hợp; `slice` trích nguyên văn đoạn ký tự của dòng output. '
          'Các hằng trong tên file, tên thuật toán, biểu thức lý thuyết và số thứ tự mục không phải kết quả đo. '
          'Bảng kết quả được kiểm tra độc lập bằng cách sinh lại từ CSV; bảng truy vết được kiểm tra bởi `verify_report.py`.']
    p.append(block('trace', table_markdown(traces, TRACE_COLUMNS)))
    write_unchanged_or_new(report_path, ('\n\n'.join(p) + '\n').encode('utf-8'), overwrite)
    write_unchanged_or_new(out_dir / 'rq2_trace.md', table_markdown(traces, TRACE_COLUMNS).encode('utf-8'), overwrite)
    return traces
