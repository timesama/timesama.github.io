---
layout: post
title:  "Downloading Images from Chrome Network via HAR"
---

1. **Enable HAR export with sensitive data**

   * Open Chrome DevTools with **F12**.
   * Press **F1** to open DevTools Settings.
   * Under **Network**, enable **Allow to generate HAR with sensitive data**.
   * This is necessary because the image requests may depend on your login/session cookies.

2. **Load all images in Network**

   * Open **DevTools → Network**.
   * Clear the existing requests if necessary.
   * Reload the webpage.
   * Scroll through/open the page until **all images have loaded**.
   * If useful, filter the Network list for the image endpoint, for example:
     `docImage.action`
   * Click a few requests and check **Preview** to confirm they contain the correct images.

3. **Export the requests as HAR**

   * In the Network request list, **right-click**.
   * Choose the HAR export option that includes **sensitive data**.
   * Save the file, for example as:
     `images.har`

   **Important:** The sensitive HAR may contain login/session cookies. Do not share it with other people.

4. **Prepare the PowerShell script**

   * Put `images.har` and the `.ps1` download script in the **same folder**.
   * Make sure the script refers to the correct HAR filename, for example:

     ```powershell
     $har = Get-Content ".\images.har" -Raw | ConvertFrom-Json
     ```

5. **Open PowerShell in that folder**

   * In Windows Explorer, open the folder containing the HAR and script.
   * Right-click inside the folder and choose **Open in Terminal**, or navigate to the folder in PowerShell.

6. **Allow scripts for this PowerShell session only**
   Run:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

   This permission lasts only until you close that PowerShell window.

7. **Run the script**
   If the script is called `download-images.ps1`, run:

   ```powershell
   .\download-images.ps1
   ```

8. **Check the downloaded images**

   * The script creates an output folder, such as:
     `images`
   * The files should appear as:
     `image_0001.jpg`
     `image_0002.jpg`
     `image_0003.jpg`
     etc.

The key point is that the **HAR with sensitive data preserves the session information Chrome uses to access the images**. Without it, requesting the `.action` URLs separately may return an HTML login/error page instead of the actual image.

**DO NOT FORGET TO REVERSE (TURN OFF HAR SENSETIVE) FROM THE STEP 1**


download-images.ps1 content be like
```
# get the har content
$har = Get-Content ".\images.har" -Raw | ConvertFrom-Json

# set the out directory
$out = ".\images"
New-Item -ItemType Directory -Force $out | Out-Null

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Import cookies from HAR
foreach ($entry in $har.log.entries) {
    try {
        $uri = [Uri]$entry.request.url

        foreach ($c in $entry.request.cookies) {
            $cookie = New-Object System.Net.Cookie
            $cookie.Name  = $c.name
            $cookie.Value = $c.value
            $cookie.Domain = $uri.Host
            $cookie.Path = "/"

            $session.Cookies.Add($uri, $cookie)
        }
    } catch {}
}

$i = 1

# run through entries and download one by one : jpg eg, png, web (add what you want in if elseif)
foreach ($entry in $har.log.entries) {

    $url = [string]$entry.request.url

    if ($url -notmatch 'docImage\.action') {
        continue
    }

    $headers = @{}

    foreach ($h in $entry.request.headers) {
        $name = [string]$h.name

        if ($name -notmatch '^(Cookie|Host|Content-Length|Connection)$') {
            $headers[$name] = [string]$h.value
        }
    }

    try {
        $r = Invoke-WebRequest `
            -Uri $url `
            -Headers $headers `
            -WebSession $session `
            -Method GET

        $type = [string]$r.Headers["Content-Type"]

        if ($type -match 'image/jpeg') {
            $ext = ".jpg"
        }
        elseif ($type -match 'image/png') {
            $ext = ".png"
        }
        elseif ($type -match 'image/webp') {
            $ext = ".webp"
        }
        else {
            Write-Host "NOT IMAGE: $type | $url"
            continue
        }

        $file = Join-Path $out ("image_{0:D4}{1}" -f $i, $ext)

        [IO.File]::WriteAllBytes(
            $file,
            $r.Content
        )

        Write-Host "Saved image_$('{0:D4}' -f $i)$ext"
        $i++
    }
    catch {
        Write-Host "FAILED: $url"
    }
}

Write-Host ""
Write-Host "Saved:" ($i - 1)
```
