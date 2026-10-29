param([Parameter(Mandatory=$true)][string]$WorkbookPath)
$ErrorActionPreference='Stop'
$target=(Resolve-Path -LiteralPath $WorkbookPath).Path
$excel=$null;$book=$null
try {
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.AutomationSecurity=3
 $book=$excel.Workbooks.Open($target,0,$false)
 if($book.ReadOnly){throw '文件只读或正被占用，不能保存打印设置'}
 foreach($sheet in $book.Worksheets){
  $sheet.PageSetup.Orientation=2
  $sheet.PageSetup.PaperSize=8
  $sheet.PageSetup.Zoom=$false
  $sheet.PageSetup.FitToPagesWide=1
  $sheet.PageSetup.FitToPagesTall=$false
 }
 $book.Save()
 Write-Output 'Excel已保存A3横向、宽一页打印设置；仍需检查实际打印预览。'
} finally {
 if($null -ne $book){$book.Close($false)}
 if($null -ne $excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
}
