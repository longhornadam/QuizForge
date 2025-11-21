from pathlib import Path
import fitz


def main():
    p = Path("dev/newspec/newspec_pdfoutputs/newspectest2.pdf")
    doc = fitz.open(p)
    print("Pages:", doc.page_count)
    for i in range(min(3, doc.page_count)):
        page = doc.load_page(i)
        text = page.get_text()
        print(f"--- Page {i+1} ---")
        print("\n".join(text.splitlines()))


if __name__ == "__main__":
    main()
