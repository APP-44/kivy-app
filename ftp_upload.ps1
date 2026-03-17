# PowerShell FTP Upload Script
$ftpServer = "ftp://211.149.140.78/"
$username = "shizhnegwheng"
$password = "63zskcx5m8kk"
$localFile = "C:\Users\Administrator\.qoderwork\workspace\mmsfmwhfvbss29v1\yang-san.php"
$remoteFile = "yang-san.php"

try {
    Write-Host "Connecting to FTP server..."

    # Create FTP request
    $ftp = [System.Net.FtpWebRequest]::Create($ftpServer + $remoteFile)
    $ftp.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $ftp.Credentials = New-Object System.Net.NetworkCredential($username, $password)
    $ftp.UseBinary = $true
    $ftp.UsePassive = $true
    $ftp.KeepAlive = $false

    # Read file content
    $content = Get-Content $localFile -Raw -Encoding UTF8
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $ftp.ContentLength = $bytes.Length

    Write-Host "Uploading file ($($bytes.Length) bytes)..."

    # Upload file
    $stream = $ftp.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()

    # Get response
    $response = $ftp.GetResponse()
    Write-Host "Upload successful!"
    Write-Host $response.StatusDescription
    $response.Close()

} catch {
    Write-Host "Error: $($_.Exception.Message)"
}
