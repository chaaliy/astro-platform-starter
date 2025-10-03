const PAGE_WIDTH = 595; // A4 width in points (72 DPI)
const PAGE_HEIGHT = 842; // A4 height in points (72 DPI)
const SCALE = 2; // render at higher resolution for sharper text
const MARGIN_X = 48;
const MARGIN_Y = 64;
const TITLE_FONT = '600 22px "Tajawal", "Cairo", "Segoe UI", "Arial", sans-serif';
const BODY_FONT = '400 16px "Tajawal", "Cairo", "Segoe UI", "Arial", sans-serif';
const TITLE_LINE_HEIGHT = 34;
const BODY_LINE_HEIGHT = 26;

const decodeBase64 = (value: string): Uint8Array => {
    const binary = atob(value);
    const output = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
        output[index] = binary.charCodeAt(index);
    }
    return output;
};

type LayoutLine = {
    text: string;
    font: string;
    lineHeight: number;
};

type RenderedPage = {
    data: Uint8Array;
    width: number;
    height: number;
};

const normalizeText = (value: string): string => value.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

const wrapParagraph = (
    context: CanvasRenderingContext2D,
    text: string,
    maxWidth: number
): string[] => {
    if (!text) {
        return [''];
    }

    const words = text.split(/\s+/).filter(Boolean);

    if (words.length === 0) {
        return [''];
    }

    const lines: string[] = [];
    let currentLine = words[0];

    for (let index = 1; index < words.length; index += 1) {
        const candidate = `${currentLine} ${words[index]}`;
        if (context.measureText(candidate).width <= maxWidth) {
            currentLine = candidate;
        } else {
            lines.push(currentLine);
            currentLine = words[index];
        }
    }

    if (context.measureText(currentLine).width <= maxWidth) {
        lines.push(currentLine);
    } else {
        let segment = '';
        Array.from(currentLine).forEach((character) => {
            const candidate = segment ? `${segment}${character}` : character;
            if (context.measureText(candidate).width <= maxWidth || segment.length === 0) {
                segment = candidate;
            } else {
                lines.push(segment);
                segment = character;
            }
        });
        if (segment) {
            lines.push(segment);
        }
    }
    return lines;
};

const prepareLayout = (
    context: CanvasRenderingContext2D,
    title: string,
    body: string
): LayoutLine[] => {
    const availableWidth = PAGE_WIDTH - MARGIN_X * 2;
    const lines: LayoutLine[] = [];

    context.font = TITLE_FONT;
    const titleLines = wrapParagraph(context, title.trim(), availableWidth);
    titleLines.forEach((line) => {
        lines.push({ text: line, font: TITLE_FONT, lineHeight: TITLE_LINE_HEIGHT });
    });

    lines.push({ text: '', font: BODY_FONT, lineHeight: BODY_LINE_HEIGHT });

    const paragraphs = normalizeText(body)
        .split('\n')
        .map((paragraph) => paragraph.trim());

    context.font = BODY_FONT;
    paragraphs.forEach((paragraph) => {
        if (paragraph.length === 0) {
            lines.push({ text: '', font: BODY_FONT, lineHeight: BODY_LINE_HEIGHT });
            return;
        }

        const wrapped = wrapParagraph(context, paragraph, availableWidth);
        wrapped.forEach((line) => {
            lines.push({ text: line, font: BODY_FONT, lineHeight: BODY_LINE_HEIGHT });
        });
        lines.push({ text: '', font: BODY_FONT, lineHeight: BODY_LINE_HEIGHT * 0.7 });
    });

    return lines;
};

const renderPages = (title: string, body: string): RenderedPage[] => {
    if (typeof document === 'undefined') {
        throw new Error('يجب استعمال هذه الوظيفة داخل المتصفح.');
    }

    const canvas = document.createElement('canvas');
    canvas.width = Math.floor(PAGE_WIDTH * SCALE);
    canvas.height = Math.floor(PAGE_HEIGHT * SCALE);
    const context = canvas.getContext('2d');

    if (!context) {
        throw new Error('متصفحك لا يدعم إنشاء ملفات PDF تلقائياً.');
    }

    context.scale(SCALE, SCALE);

    const resetPage = () => {
        context.setTransform(1, 0, 0, 1, 0, 0);
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.setTransform(SCALE, 0, 0, SCALE, 0, 0);
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, PAGE_WIDTH, PAGE_HEIGHT);
        context.fillStyle = '#0f172a';
        context.textAlign = 'right';
        context.textBaseline = 'top';
        context.direction = 'rtl';
    };

    resetPage();

    const lines = prepareLayout(context, title, body);
    const pages: RenderedPage[] = [];
    const usableHeight = PAGE_HEIGHT - MARGIN_Y;
    let cursorY = MARGIN_Y;
    let hasContentOnPage = false;

    const commitPage = (force = false) => {
        if (!force && !hasContentOnPage) {
            return;
        }
        const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
        const base64Data = dataUrl.split(',')[1] ?? '';
        pages.push({ data: decodeBase64(base64Data), width: PAGE_WIDTH, height: PAGE_HEIGHT });
        resetPage();
        cursorY = MARGIN_Y;
        hasContentOnPage = false;
    };

    lines.forEach((line) => {
        const nextLineBottom = cursorY + line.lineHeight;
        if (nextLineBottom > usableHeight) {
            commitPage(true);
        }
        if (line.text.trim().length > 0) {
            context.font = line.font;
            context.fillText(line.text, PAGE_WIDTH - MARGIN_X, cursorY);
            hasContentOnPage = true;
        } else {
            // احتسب الأسطر الفارغة للحفاظ على المسافات
            hasContentOnPage = true;
        }
        cursorY = cursorY + line.lineHeight;
    });

    commitPage(hasContentOnPage || pages.length === 0);
    canvas.remove();

    return pages;
};

const encoder = new TextEncoder();

const getPartLength = (part: string | Uint8Array): number =>
    typeof part === 'string' ? encoder.encode(part).length : part.length;

export const createPdf = (title: string, body: string): Blob => {
    const pages = renderPages(title, body);

    if (pages.length === 0) {
        throw new Error('تعذر إنشاء الصفحات المطلوبة للوثيقة.');
    }

    type PdfObject = {
        id: number;
        parts: (string | Uint8Array)[];
    };

    const objects: PdfObject[] = [];
    const kids: number[] = [];

    let nextId = 3;
    pages.forEach((page, index) => {
        const pageId = nextId;
        const imageId = nextId + 1;
        const contentId = nextId + 2;
        nextId += 3;

        kids.push(pageId);
        const imageName = `/Im${index + 1}`;

        objects.push({
            id: imageId,
            parts: [
                `<< /Type /XObject /Subtype /Image /Width ${page.width} /Height ${page.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${page.data.length} >>\nstream\n`,
                page.data,
                '\nendstream\n'
            ]
        });

        const contentStream = `q ${page.width} 0 0 ${page.height} 0 0 cm ${imageName} Do Q`;
        objects.push({
            id: contentId,
            parts: [`<< /Length ${encoder.encode(contentStream).length} >>\nstream\n${contentStream}\nendstream\n`]
        });

        objects.push({
            id: pageId,
            parts: [
                `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${page.width} ${page.height}] /Resources << /XObject << ${imageName} ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>\n`
            ]
        });
    });

    objects.push({
        id: 2,
        parts: [`<< /Type /Pages /Kids [${kids.map((kid) => `${kid} 0 R`).join(' ')}] /Count ${pages.length} >>\n`]
    });

    objects.push({ id: 1, parts: ['<< /Type /Catalog /Pages 2 0 R >>\n'] });

    const sortedObjects = objects.sort((a, b) => a.id - b.id);
    const header = '%PDF-1.4\n';
    const blobParts: (string | Uint8Array)[] = [header];
    let offset = encoder.encode(header).length;
    const offsets: Record<number, number> = {};

    sortedObjects.forEach((object) => {
        offsets[object.id] = offset;
        const objectHeader = `${object.id} 0 obj\n`;
        blobParts.push(objectHeader);
        offset += getPartLength(objectHeader);

        object.parts.forEach((part) => {
            blobParts.push(part);
            offset += getPartLength(part);
        });

        const objectFooter = 'endobj\n';
        blobParts.push(objectFooter);
        offset += getPartLength(objectFooter);
    });

    const highestId = sortedObjects[sortedObjects.length - 1]?.id ?? 2;
    const xrefStart = offset;
    let xref = `xref\n0 ${highestId + 1}\n`;
    xref += '0000000000 65535 f \n';
    for (let id = 1; id <= highestId; id += 1) {
        const value = offsets[id] ?? 0;
        xref += `${value.toString().padStart(10, '0')} 00000 n \n`;
    }
    blobParts.push(xref);

    const trailer = `trailer\n<< /Size ${highestId + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF`;
    blobParts.push(trailer);

    return new Blob(blobParts, { type: 'application/pdf' });
};
