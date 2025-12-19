---
description: Export Research Slides to PDF
---

**Use this command to export ANY Research Infographic to a PDF Carousel.**

### Usage
Run the command with the path to your research file (or just the slug):
`@[/export-pdf]@[src/content/research/research-antifragile-mev-infrastructure.mdx]`

### Step 1: Open the Slide View
The system will generate a dynamic link based on your input:
*   **Path:** `/slides/[slug]`
*   **Example Link:** [Open Slide View for Antifragile MEV](http://localhost:4321/slides/research-antifragile-mev-infrastructure)

*(Replace the slug in the URL with your specific research file's slug if different)*

### Step 2: Print to PDF (Chrome/Edge Required)
1.  Open the link in **Chrome** or **Edge**.
2.  Press `Cmd + P` (or `Ctrl + P`).
3.  **Destination**: Save as PDF.
4.  **Layout**: Portrait.
5.  **Margins**: **None** (CRITICAL).
6.  **Options**: Check **"Background graphics"** (CRITICAL).
7.  **Pages**: The slides will appear first. **Print only pages 1-X** (where X is the number of slides). Ignore the text pages that follow.

### Troubleshooting
*   **Charts Blank?** Refresh the page once before printing.
*   **Not a Slide Layout?** Ensure the URL starts with `/slides/`.
