$ErrorActionPreference='Stop'
$dir='E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.2_分组阅读版'
$app=$null;$book=$null
try {
 $app=New-Object -ComObject Excel.Application
 $app.Visible=$false;$app.DisplayAlerts=$false;$app.AutomationSecurity=3
 $book=$app.Workbooks.Open((Join-Path $dir '剧本资产需求清单.xlsx'),0,$true)
 if($book.Worksheets.Count -ne 3){throw '工作表数量不符'}
 $counts=@()
 foreach($sheet in $book.Worksheets){
  $table=$sheet.ListObjects.Item(1)
  if($table.ListColumns.Count -ne 5 -or -not $table.ShowAutoFilter){throw '列数或筛选不符'}
  $counts += $table.ListRows.Count
 }
 if(($counts -join ',') -ne '25,56,48'){throw '行数不符'}
 if($book.Worksheets.Item('角色').Range('A7').Value2 -ne 'R01-01'){throw '角色子项未跟随'}
 $result=[ordered]@{engine='Microsoft Excel COM';readOnly=$true;sheets=3;columnsPerSheet=5;rows=$counts;filters=$true;roleChildAfterParent=$true}
 $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'Excel原生验证.json') -Encoding utf8
 $result | ConvertTo-Json -Compress
}finally{
 if($null -ne $book){$book.Close($false)}
 if($null -ne $app){$app.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
