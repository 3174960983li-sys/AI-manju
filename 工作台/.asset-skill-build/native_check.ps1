$ErrorActionPreference='Stop'
$sample='E:\AI漫剧\04_项目管理\02_任务记录\剧本资产拆解_首轮小样\样稿\剧本资产需求清单.xlsx'
$temporary=Join-Path $PSScriptRoot 'native-sandbox.xlsx'
Copy-Item -LiteralPath $sample -Destination $temporary -Force
$app=$null
$book=$null
try {
  $app=New-Object -ComObject Excel.Application
  $app.Visible=$false
  $app.DisplayAlerts=$false
  $app.AutomationSecurity=3
  $book=$app.Workbooks.Open($temporary,0,$false)
  if($book.Worksheets.Count -ne 7){throw '工作表数错误'}
  $app.CalculateFull()
  $overview=$book.Worksheets.Item('使用说明与总览')
  $counts=@()
  for($r=11;$r -le 16;$r++){$counts+= [int]$overview.Cells.Item($r,2).Value2}
  if(($counts -join ',') -ne '7,8,1,3,2,20'){throw "原生统计错误 $counts"}
  $characters=$book.Worksheets.Item('角色基础')
  $table=$characters.ListObjects.Item('AssetsCHR')
  if(-not $table.ShowAutoFilter){throw '筛选未开启'}
  $before=$book.Names.Item('asset_CHR_0001').RefersToRange.Address()
  $characters.Range('A5:R11').Sort($characters.Range('A5'),2)
  $app.CalculateFull()
  $after=$book.Names.Item('asset_CHR_0001').RefersToRange.Address()
  if($before -eq $after){throw '排序后动态定位没有变化'}
  if($book.Names.Item('asset_CHR_0001').RefersToRange.Value2 -ne 'CHR-0001'){throw '动态定位错误'}
  $added=$table.ListRows.Add()
  $added.Range.Cells.Item(1,1).Value2='CHR-0099'
  $added.Range.Cells.Item(1,17).Value2='有效'
  $app.CalculateFull()
  if([int]$overview.Range('B11').Value2 -ne 8){throw '新增表行后统计未扩展'}
  $result=[ordered]@{engine='Microsoft Excel COM';opened=$true;counts=$counts;filter=$true;dynamicNameBefore=$before;dynamicNameAfter=$after;newRowCount=[int]$overview.Range('B11').Value2;sourceUnchanged=$true}
  $result | ConvertTo-Json | Set-Content -LiteralPath 'E:\AI漫剧\04_项目管理\02_任务记录\剧本资产拆解_首轮小样\Excel原生验证.json' -Encoding utf8
  $result | ConvertTo-Json -Compress
} finally {
  if($null -ne $book){$book.Close($false)}
  if($null -ne $app){$app.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
}
