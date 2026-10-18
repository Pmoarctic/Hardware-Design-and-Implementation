"""Windows QA fallback when the packaged renderer has no LibreOffice."""
from pathlib import Path
import win32com.client
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
source=HERE.parent/'stopwatch-interrupt-th.docx'
out=HERE/'render'
out.mkdir(exist_ok=True)
pdf=out/'stopwatch-interrupt-th.pdf'
word=win32com.client.DispatchEx('Word.Application')
word.Visible=False
word.DisplayAlerts=0
document=None
try:
    document=word.Documents.Open(str(source),ReadOnly=True,AddToRecentFiles=False)
    document.Repaginate()
    print('Word page count:',document.ComputeStatistics(2))
    document.ExportAsFixedFormat(str(pdf),17)
finally:
    if document is not None:document.Close(False)
    word.Quit()
rendered=pdfium.PdfDocument(str(pdf))
print('PDF page count:',len(rendered))
for index in range(len(rendered)):
    page=rendered[index]
    page.render(scale=2).to_pil().save(out/f'page-{index+1}.png')
    page.close()
rendered.close()
