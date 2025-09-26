"c:\Program Files\Python311\python.exe" create_version.py
SET /P MyVar=< folder.txt
"%MyVar%\blender.exe" --command extension build
"c:\Program Files\Pandoc\pandoc.exe" README.md -o README.pdf --pdf-engine="c:\Program Files\wkhtmltopdf\bin\wkhtmltopdf"  --css pdf.css
move *.zip zips