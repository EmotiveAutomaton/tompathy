# Regenerate the checked-in app sizes after replacing the supplied master.
# Run from the project root: powershell -File scripts/resize-icons.ps1
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectPath = Split-Path -Parent $PSScriptRoot
$source = [System.Drawing.Bitmap]::new((Join-Path $projectPath 'src/assets/icon-master.png'))
$smallSource = [System.Drawing.Bitmap]::new((Join-Path $projectPath 'src/assets/icon-small-master.png'))
try {
    foreach ($size in @(16, 32, 48, 128)) {
        $inputImage = if ($size -le 32) { $smallSource } else { $source }
        $bitmap = [System.Drawing.Bitmap]::new($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $attributes = [System.Drawing.Imaging.ImageAttributes]::new()
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $attributes.SetWrapMode([System.Drawing.Drawing2D.WrapMode]::TileFlipXY)
            $graphics.DrawImage($inputImage, [System.Drawing.Rectangle]::new(0, 0, $size, $size), 0, 0, $inputImage.Width, $inputImage.Height, [System.Drawing.GraphicsUnit]::Pixel, $attributes)
            $bitmap.Save((Join-Path $projectPath "public/icon$size.png"), [System.Drawing.Imaging.ImageFormat]::Png)
        } finally {
            $attributes.Dispose()
            $graphics.Dispose()
            $bitmap.Dispose()
        }
    }
} finally { $source.Dispose(); $smallSource.Dispose() }
