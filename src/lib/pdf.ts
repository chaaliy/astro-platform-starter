const escapePdfText = (value: string): string => value.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');

const toLines = (title: string, body: string): string[] => {
    const normalizedBody = body.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const bodyLines = normalizedBody.split('\n').map((line) => line.trimEnd());
    const lines: string[] = [];
    lines.push(title);
    lines.push('');
    lines.push(...bodyLines);
    return lines;
};

export const createPdf = (title: string, body: string): Blob => {
    const header = '%PDF-1.4\n';
    const lines = toLines(title, body);
    const linesPerPage = 38;
    const pages: string[][] = [];

    for (let index = 0; index < lines.length; index += linesPerPage) {
        pages.push(lines.slice(index, index + linesPerPage));
    }

    if (pages.length === 0) {
        pages.push(['']);
    }

    const objects: { id: number; body: string }[] = [];
    const kids: string[] = [];

    pages.forEach((pageLines, index) => {
        const pageId = 3 + index * 2;
        const contentId = pageId + 1;
        kids.push(`${pageId} 0 R`);
        const textOperators = ['BT', '/F1 16 Tf', '1 0 0 1 520 780 Tm', '-16 TL'];
        pageLines.forEach((line, lineIndex) => {
            const clean = escapePdfText(line || ' ');
            if (lineIndex === 0) {
                textOperators.push(`(${clean}) Tj`);
            } else {
                textOperators.push(`T* (${clean}) Tj`);
            }
        });
        textOperators.push('ET');
        const stream = textOperators.join('\n');
        const encodedLength = new TextEncoder().encode(stream).length;
        objects.push({ id: contentId, body: `<< /Length ${encodedLength} >>\nstream\n${stream}\nendstream` });
        objects.push({
            id: pageId,
            body: `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents ${contentId} 0 R /Resources << /Font << /F1 ${
                3 + pages.length * 2
            } 0 R >> >> >>`
        });
    });

    const fontId = 3 + pages.length * 2;
    objects.push({ id: fontId, body: '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>' });
    objects.push({ id: 2, body: `<< /Type /Pages /Kids [${kids.join(' ')}] /Count ${pages.length} >>` });
    objects.push({ id: 1, body: '<< /Type /Catalog /Pages 2 0 R >>' });

    const encoder = new TextEncoder();
    let offset = encoder.encode(header).length;
    const xref: string[] = [];
    const bodyParts: string[] = [header];
    const offsets: Record<number, number> = {};

    const sortedObjects = objects.sort((a, b) => a.id - b.id);

    sortedObjects.forEach((obj) => {
        const objectString = `${obj.id} 0 obj\n${obj.body}\nendobj\n`;
        offsets[obj.id] = offset;
        bodyParts.push(objectString);
        offset += encoder.encode(objectString).length;
    });

    const highestId = sortedObjects[sortedObjects.length - 1]?.id ?? 0;
    const xrefHeader = `xref\n0 ${highestId + 1}\n`;
    bodyParts.push(xrefHeader);
    xref.push('0000000000 65535 f ');
    for (let i = 1; i <= highestId; i += 1) {
        const value = offsets[i] ?? 0;
        xref.push(`${value.toString().padStart(10, '0')} 00000 n `);
    }
    const xrefBody = xref.join('\n') + '\n';
    bodyParts.push(xrefBody);
    const trailer = `trailer\n<< /Size ${highestId + 1} /Root 1 0 R >>\nstartxref\n${offset}\n%%EOF`;
    bodyParts.push(trailer);

    return new Blob(bodyParts, { type: 'application/pdf' });
};
