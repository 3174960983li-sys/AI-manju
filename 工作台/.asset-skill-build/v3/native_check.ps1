$ErrorActionPreference='Stop'
$dir='E:\AI漫剧\01_作品项目\保镖驾到\资产需求\原剧第1—10集_资产拆解_V3'
$audit=Join-Path $dir '核验资料'
New-Item -ItemType Directory -Path $audit -Force | Out-Null
$layout=Get-Content -LiteralPath (Join-Path $dir '版面与原文索引.json') -Raw -Encoding utf8 | ConvertFrom-Json
$app=$null;$book=$null
try {
 $app=New-Object -ComObject Excel.Application
 $app.Visible=$false;$app.DisplayAlerts=$false;$app.AutomationSecurity=3
 $book=$app.Workbooks.Open((Join-Path $dir '剧本资产需求清单.xlsx'),0,$true)
 if($book.Worksheets.Count -ne 3){throw '工作表数量错误'}
 $verified=@()
 foreach($entry in $layout.sheets){
  $sheet=$book.Worksheets.Item($entry.name)
  if($sheet.UsedRange.Columns.Count -ne 5){throw '列数错误'}
  if(-not $sheet.AutoFilterMode){throw '筛选缺失'}
  if($sheet.Outline.SummaryRow -ne 0){throw '摘要行没有位于原文上方'}
  foreach($asset in $entry.assets){
   if($sheet.Rows.Item([int]$asset.master).Hidden){throw ('主行被隐藏：'+$asset.id)}
   foreach($raw in $asset.raw){if(-not $sheet.Rows.Item([int]$raw.row).Hidden){throw '原文没有默认折叠'}}
  }
  $first=$entry.groups[0]
  if($null -ne $first){
   $sheet.Rows.Item([int]$first.master).ShowDetail=$true
   if($sheet.Rows.Item([int]$first.first).Hidden){throw '原文无法展开'}
   if($entry.assets.Count -gt 1 -and $sheet.Rows.Item([int]$entry.assets[1].master).Hidden){throw '展开原文影响后续子资产'}
   $sheet.Rows.Item([int]$first.master).ShowDetail=$false
   if(-not $sheet.Rows.Item([int]$first.first).Hidden){throw '原文无法重新收起'}
  }
  $sheet.Activate()
  if(-not $app.ActiveWindow.FreezePanes -or $app.ActiveWindow.SplitRow -ne 5 -or $app.ActiveWindow.SplitColumn -ne 2){throw '冻结位置错误'}
  if($sheet.PageSetup.Orientation -ne 2 -or $sheet.PageSetup.PaperSize -ne 8){throw '打印纸型错误'}
  $verified += [ordered]@{sheet=$entry.name;assets=$entry.assets.Count;rawGroups=$entry.groups.Count;collapsedByDefault=$true;expandCollapse=$true;subAssetsVisible=$true;filter=$true;freeze='C6';print='A3横向'}
 }
 # Native print preview substitute: export exactly what Excel would print with default collapsed rows.
 $book.ExportAsFixedFormat(0,(Join-Path $audit '默认收起_打印核验.pdf'))
 $roles=$book.Worksheets.Item('角色');$first=$layout.sheets[0].groups[0]
 $roles.Rows.Item([int]$first.master).ShowDetail=$true
 $roles.PageSetup.PrintArea='A1:E'+$first.last
 $roles.ExportAsFixedFormat(0,(Join-Path $audit '角色原文展开_打印核验.pdf'))
 $roles.Rows.Item([int]$first.master).ShowDetail=$false
 $result=[ordered]@{engine='Microsoft Excel COM';readOnly=$true;sheets=$verified;defaultPrintPdf=$true;expandedPrintPdf=$true;sourceWorkbookSaved=$false}
 $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $audit 'Excel原生验证.json') -Encoding utf8
 $result | ConvertTo-Json -Depth 5 -Compress
} finally {
 if($null -ne $book){$book.Close($false)}
 if($null -ne $app){$app.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
