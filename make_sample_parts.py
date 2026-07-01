from openpyxl import Workbook

wb = Workbook()
sheet = wb.active
sheet.title = "部品マスタ"

headers = ["部品名", "型番", "価格(円)", "用途", "互換品", "メモ"]
sheet.append(headers)

rows = [
    ["ザボゾボ", "XYZ-100", 15000, "農業機械の動力伝達部", "ZBZ-100S", "耐久性が高い"],
    ["ザボゾボ", "XYZ-200", 18500, "大型農業機械用", "なし", "XYZ-100の後継品"],
    ["ガスコンキーザー", "A200", 8500, "小型エンジン用ガス圧縮部品", "B300", ""],
    ["ガスコンキーザー", "A300", 9200, "中型エンジン用", "A200(下位互換)", "A200より耐熱性向上"],
    ["ベアリング", "BR-50", 3200, "回転部分の軸受け", "BR-50S", "寿命約2年"],
]
for row in rows:
    sheet.append(row)

for col, width in zip("ABCDEF", [16, 12, 10, 28, 16, 24]):
    sheet.column_dimensions[col].width = width

wb.save(r"C:\Users\ename\Desktop\rag_app\parts_master.xlsx")
print("作成完了")
