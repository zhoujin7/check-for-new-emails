Get-CimInstance -ClassName Win32_Process |
Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*check_for_new_emails.py*' } |
ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
} 
