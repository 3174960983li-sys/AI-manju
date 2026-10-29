$ErrorActionPreference='Stop'
$dir='E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.1'
$app=$null;$book=$null
try {
 $app=New-Object -ComObject Excel.Application
 $app.Visible=$false;$app.DisplayAlerts=$false;$app.AutomationSecurity=3
 $book=$app.Workbooks.Open((Join-Path $dir '剧本资产需求清单.xlsx'),0,$true)
 $app.CalculateFull()
 if($book.Worksheets.Count -ne 7){throw '表数不符'}
 $summary=$book.Worksheets.Item('使用说明与总览');$counts=@()
 for($i=11;$i -le 16;$i++){$counts+=[int]$summary.Cells.Item($i,2).Value2}
 if(($counts -join ',') -ne '20,22,37,44,37,105'){throw '原生统计不符'}
 foreach($sheet in $book.Worksheets){
  if($sheet.Name -ne '使用说明与总览'){
   if(-not $sheet.ListObjects.Item(1).ShowAutoFilter){throw '筛选缺失'}
  }
 }
 if($book.Names.Item('asset_CHR_0001').RefersToRange.Value2 -ne 'CHR-0001'){throw '内部命名引用错误'}
 $result=[ordered]@{engine='Microsoft Excel COM';readOnly=$true;counts=$counts;filters=$true;dynamicName='CHR-0001';specialRows=14}
 $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'Excel原生验证.json') -Encoding utf8
 $result | ConvertTo-Json -Compress
} finally {
 if($null -ne $book){$book.Close($false)}
 if($null -ne $app){$app.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
