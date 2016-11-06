# pdf2graphs
Python script for converting graphs in vector graphics format inside a PDF into a node and edge list in JSON format

To run, use:
./pdf2graphs filename.pdf
with filename.pdf replaced with the desired pdf file.  This will produce .png files of the detected graphs on each page, along with .json files containing the graphs for each page.  Pages where no graphs were detected are not printed.
