import { type FormEvent, useMemo, useState } from 'react';

type FieldType = 'text' | 'textarea' | 'date' | 'number' | 'email';

type DocumentField = {
    name: string;
    label: string;
    type: FieldType;
    placeholder?: string;
    helper?: string;
    required?: boolean;
    rows?: number;
};

type DocumentDefinition = {
    id: string;
    name: string;
    description: string;
    fields: DocumentField[];
};

type FormState = Record<string, string>;

type GenerationState =
    | { status: 'idle' }
    | { status: 'loading' }
    | { status: 'error'; message: string }
    | { status: 'done'; content: string };

const DOCUMENT_DEFINITIONS: DocumentDefinition[] = [
    {
        id: 'annualActionPlan',
        name: 'خطة العمل السنوية',
        description: 'حدد أهداف وأنشطة الجمعية للسنة المقبلة مع مؤشرات المتابعة.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'year', label: 'السنة', type: 'number', placeholder: '2025', required: true },
            { name: 'strategicObjectives', label: 'الأهداف الاستراتيجية', type: 'textarea', rows: 4, required: true },
            { name: 'mainProjects', label: 'المشاريع الرئيسية', type: 'textarea', rows: 4, required: true },
            { name: 'keyPartners', label: 'الشركاء الرئيسيون', type: 'textarea', rows: 3 },
            { name: 'monitoringApproach', label: 'منهجية المتابعة والتقييم', type: 'textarea', rows: 3 }
        ]
    },
    {
        id: 'annualBudget',
        name: 'الميزانية السنوية',
        description: 'أنشئ تقديراً مفصلاً للإيرادات والنفقات المتوقعة للسنة.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'year', label: 'السنة المالية', type: 'number', required: true },
            { name: 'incomeSources', label: 'مصادر التمويل المتوقعة', type: 'textarea', rows: 4, required: true },
            { name: 'expenseCategories', label: 'أبواب الصرف', type: 'textarea', rows: 4, required: true },
            { name: 'cashflowNotes', label: 'ملاحظات حول التدفقات المالية', type: 'textarea', rows: 3 }
        ]
    },
    {
        id: 'rfq',
        name: 'طلب عرض أسعار',
        description: 'جهز نموذجاً رسمياً للتواصل مع الموردين وطلب عروض الأسعار.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'projectName', label: 'اسم المشروع', type: 'text', required: true },
            { name: 'itemDescription', label: 'وصف الخدمات أو السلع المطلوبة', type: 'textarea', rows: 4, required: true },
            { name: 'deliveryDate', label: 'تاريخ التسليم المتوقع', type: 'date', required: true },
            { name: 'contactPerson', label: 'اسم مسؤول الاتصال', type: 'text', required: true },
            { name: 'contactEmail', label: 'البريد الإلكتروني للتواصل', type: 'email', required: true }
        ]
    },
    {
        id: 'purchaseOrder',
        name: 'أمر شراء',
        description: 'وثّق قرار الشراء والمصادقة عليه مع تفاصيل المورد والشروط.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'supplierName', label: 'اسم المورد', type: 'text', required: true },
            { name: 'orderItems', label: 'تفاصيل المشتريات (الكمية، السعر، الوحدة)', type: 'textarea', rows: 4, required: true },
            { name: 'orderDate', label: 'تاريخ إصدار الأمر', type: 'date', required: true },
            { name: 'deliveryTerms', label: 'شروط التسليم', type: 'textarea', rows: 3 },
            { name: 'paymentTerms', label: 'شروط الأداء', type: 'textarea', rows: 3 }
        ]
    },
    {
        id: 'invoice',
        name: 'فاتورة',
        description: 'أنشئ فاتورة احترافية للموردين أو الشركاء.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'invoiceNumber', label: 'رقم الفاتورة', type: 'text', required: true },
            { name: 'invoiceDate', label: 'تاريخ الإصدار', type: 'date', required: true },
            { name: 'clientName', label: 'اسم الزبون أو الشريك', type: 'text', required: true },
            { name: 'servicesRendered', label: 'الخدمات أو السلع المقدمة', type: 'textarea', rows: 4, required: true },
            { name: 'totalAmount', label: 'المبلغ الإجمالي', type: 'text', required: true }
        ]
    },
    {
        id: 'bidOpening',
        name: 'محضر فتح الأظرفة',
        description: 'سجل تفاصيل جلسة فتح العروض مع الحضور والملاحظات.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'sessionDate', label: 'تاريخ الجلسة', type: 'date', required: true },
            { name: 'committeeMembers', label: 'أعضاء اللجنة الحاضرون', type: 'textarea', rows: 3, required: true },
            { name: 'bidders', label: 'لائحة العارضين', type: 'textarea', rows: 4, required: true },
            { name: 'observations', label: 'الملاحظات والقرارات', type: 'textarea', rows: 4 }
        ]
    },
    {
        id: 'receptionReport',
        name: 'محضر الاستلام',
        description: 'وثّق استلام السلع أو الخدمات بعد التحقق من جودتها.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'projectName', label: 'المشروع أو الصفقة', type: 'text', required: true },
            { name: 'receptionDate', label: 'تاريخ الاستلام', type: 'date', required: true },
            { name: 'receivedItems', label: 'المواد أو الخدمات المستلمة', type: 'textarea', rows: 4, required: true },
            { name: 'qualityNotes', label: 'ملاحظات حول الجودة والالتزام', type: 'textarea', rows: 4 }
        ]
    },
    {
        id: 'narrativeReport',
        name: 'التقرير السردي السنوي',
        description: 'لخص أبرز إنجازات الجمعية وتأثير أنشطتها خلال السنة.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'year', label: 'السنة المرجعية', type: 'number', required: true },
            { name: 'missionSummary', label: 'ملخص رسالة الجمعية', type: 'textarea', rows: 3, required: true },
            { name: 'majorAchievements', label: 'أهم الإنجازات', type: 'textarea', rows: 4, required: true },
            { name: 'beneficiaries', label: 'الفئات المستفيدة', type: 'textarea', rows: 3, required: true },
            { name: 'challenges', label: 'التحديات والدروس المستفادة', type: 'textarea', rows: 4 }
        ]
    },
    {
        id: 'financialReport',
        name: 'التقرير المالي السنوي',
        description: 'قدّم تحليلاً للنتائج المالية مع مقارنة بالميزانية.',
        fields: [
            { name: 'associationName', label: 'اسم الجمعية', type: 'text', required: true },
            { name: 'year', label: 'السنة المالية', type: 'number', required: true },
            { name: 'incomeSummary', label: 'ملخص الإيرادات المحققة', type: 'textarea', rows: 4, required: true },
            { name: 'expenseSummary', label: 'ملخص المصاريف', type: 'textarea', rows: 4, required: true },
            { name: 'fundingGaps', label: 'الفجوات أو الفوائض التمويلية', type: 'textarea', rows: 3 },
            { name: 'recommendations', label: 'التوصيات المالية', type: 'textarea', rows: 3 }
        ]
    }
];

const defaultFormState = (definition: DocumentDefinition): FormState =>
    definition.fields.reduce<FormState>((acc, field) => {
        acc[field.name] = '';
        return acc;
    }, {});

const escapePdfText = (value: string): string => value.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');

const createPdf = (title: string, body: string): Blob => {
    const header = '%PDF-1.4\n';
    const lines = [title, '', ...body.split('\n')];
    const linesPerPage = 40;
    const pages: string[][] = [];

    for (let i = 0; i < lines.length; i += linesPerPage) {
        pages.push(lines.slice(i, i + linesPerPage));
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
        const textOperators = ['BT', '/F1 14 Tf', '1 0 0 1 60 780 Tm', '16 TL'];
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

    const sortedObjects = objects.sort((a, b) => a.id - b.id);
    const encoder = new TextEncoder();
    let offset = encoder.encode(header).length;
    const xref: string[] = [];
    const bodyParts: string[] = [header];
    const offsets: Record<number, number> = {};

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
    const pdfString = bodyParts.join('');
    return new Blob([pdfString], { type: 'application/pdf' });
};

const buildDocumentContent = (definition: DocumentDefinition, formValues: FormState): string => {
    const sections: string[] = [];
    const name = definition.name;
    const association = formValues.associationName ? `جمعية ${formValues.associationName}` : 'الجمعية';

    switch (definition.id) {
        case 'annualActionPlan':
            sections.push(
                `${association} تقدم خطة عمل مفصلة لسنة ${formValues.year}. تستند الخطة إلى الأهداف الاستراتيجية التالية: ${formValues.strategicObjectives}.`
            );
            sections.push(`المشاريع الرئيسية المبرمجة تشمل: ${formValues.mainProjects}.`);
            if (formValues.keyPartners) {
                sections.push(`سيتم تنفيذ الأنشطة بشراكة مع: ${formValues.keyPartners}.`);
            }
            if (formValues.monitoringApproach) {
                sections.push(`منهجية المتابعة والتقييم المعتمدة: ${formValues.monitoringApproach}.`);
            }
            sections.push('يتم تتبع المؤشرات بشكل دوري لضمان تحقيق النتائج المتوقعة وتعزيز الأثر المجتمعي.');
            break;
        case 'annualBudget':
            sections.push(
                `${association} تعرض تقديراً للميزانية الخاصة بسنة ${formValues.year}. وتشمل الموارد المالية المتوقعة: ${formValues.incomeSources}.`
            );
            sections.push(`برمجت المصاريف على الأبواب التالية: ${formValues.expenseCategories}.`);
            if (formValues.cashflowNotes) {
                sections.push(`ملاحظات إضافية حول التدفقات المالية: ${formValues.cashflowNotes}.`);
            }
            sections.push('يتم مراقبة التنفيذ المالي بشكل شهري مع مقارنة دورية بالميزانية التقديرية.');
            break;
        case 'rfq':
            sections.push(`تعلن ${association} عن رغبتها في الحصول على عروض أسعار في إطار مشروع ${formValues.projectName}.`);
            sections.push(`يشمل نطاق الطلب: ${formValues.itemDescription}.`);
            sections.push(`يتعين على الموردين احترام تاريخ التسليم المحدد في ${formValues.deliveryDate}.`);
            sections.push(
                `لمزيد من المعلومات، يرجى التواصل مع ${formValues.contactPerson} عبر البريد الإلكتروني ${formValues.contactEmail}.`
            );
            sections.push('يجب أن تتضمن العروض تفاصيل الأسعار، شروط الأداء، ومدة صلاحية العرض.');
            break;
        case 'purchaseOrder':
            sections.push(`تصدر ${association} أمر شراء لفائدة المورد ${formValues.supplierName}.`);
            sections.push(`تفاصيل المشتريات المطلوبة: ${formValues.orderItems}.`);
            sections.push(`تم توقيع الأمر بتاريخ ${formValues.orderDate}.`);
            if (formValues.deliveryTerms) {
                sections.push(`شروط التسليم المتفق عليها: ${formValues.deliveryTerms}.`);
            }
            if (formValues.paymentTerms) {
                sections.push(`شروط الأداء: ${formValues.paymentTerms}.`);
            }
            sections.push('يعد هذا الأمر التزاماً قانونياً بتنفيذ الصفقة وفق المواصفات المتفق عليها.');
            break;
        case 'invoice':
            sections.push(`تصدر ${association} هذه الفاتورة برقم ${formValues.invoiceNumber} بتاريخ ${formValues.invoiceDate}.`);
            sections.push(`الزبون: ${formValues.clientName}.`);
            sections.push(`تفاصيل الخدمات أو السلع المقدمة: ${formValues.servicesRendered}.`);
            sections.push(`المبلغ الإجمالي المستحق: ${formValues.totalAmount}.`);
            sections.push('يرجى أداء المبلغ في الآجال القانونية مع الإشارة إلى رقم الفاتورة في عملية التحويل.');
            break;
        case 'bidOpening':
            sections.push(`بتاريخ ${formValues.sessionDate} عقدت ${association} جلسة فتح الأظرفة الخاصة بالصفقات.`);
            sections.push(`حضر الجلسة أعضاء اللجنة التالية: ${formValues.committeeMembers}.`);
            sections.push(`تمت دراسة عروض مقدمة من: ${formValues.bidders}.`);
            if (formValues.observations) {
                sections.push(`خلاصة الملاحظات والقرارات: ${formValues.observations}.`);
            }
            sections.push('تم تحرير هذا المحضر للتوقيع من قبل جميع الأعضاء الحاضرين واعتماده من طرف المكتب المسير.');
            break;
        case 'receptionReport':
            sections.push(`في إطار مشروع ${formValues.projectName} تم بتاريخ ${formValues.receptionDate} استلام السلع أو الخدمات.`);
            sections.push(`يشمل الاستلام العناصر التالية: ${formValues.receivedItems}.`);
            if (formValues.qualityNotes) {
                sections.push(`تم تسجيل الملاحظات التالية حول الجودة والالتزام: ${formValues.qualityNotes}.`);
            }
            sections.push('يؤكد هذا المحضر مطابقة المقتنيات للمواصفات المعتمدة ويمنح الإذن بصرف المستحقات وفقاً للإجراءات.');
            break;
        case 'narrativeReport':
            sections.push(`يقدم هذا التقرير نظرة شاملة حول أنشطة ${association} خلال سنة ${formValues.year}.`);
            sections.push(`تعتمد الجمعية على رسالتها: ${formValues.missionSummary}.`);
            sections.push(`أهم الإنجازات المسجلة: ${formValues.majorAchievements}.`);
            sections.push(`استفادت الفئات التالية من تدخلات الجمعية: ${formValues.beneficiaries}.`);
            if (formValues.challenges) {
                sections.push(`واجهت الجمعية التحديات التالية مع الدروس المستخلصة: ${formValues.challenges}.`);
            }
            sections.push('تواصل الجمعية تعزيز شراكاتها لضمان استدامة البرامج وتحسين جودة الخدمات المقدمة.');
            break;
        case 'financialReport':
            sections.push(`يعرض هذا التقرير الوضعية المالية لـ${association} خلال سنة ${formValues.year}.`);
            sections.push(`الإيرادات المحققة: ${formValues.incomeSummary}.`);
            sections.push(`المصاريف المسجلة: ${formValues.expenseSummary}.`);
            if (formValues.fundingGaps) {
                sections.push(`الفجوات أو الفوائض التمويلية: ${formValues.fundingGaps}.`);
            }
            if (formValues.recommendations) {
                sections.push(`التوصيات المعتمدة لتحسين التدبير المالي: ${formValues.recommendations}.`);
            }
            sections.push('يعتمد التقرير على مبادئ الحكامة المالية والشفافية مع إرفاق الوثائق التبريرية عند الحاجة.');
            break;
        default:
            sections.push(`${association} تقدم هذا المستند وفقاً للمعطيات المدخلة.`);
    }

    return sections.join('\n\n');
};

const generateDocument = async (definition: DocumentDefinition, formValues: FormState): Promise<string> => {
    // In a production setting this is where a generative AI service would be invoked.
    // We simulate latency to mimic an asynchronous call and produce structured Arabic content.
    await new Promise((resolve) => setTimeout(resolve, 650));
    return buildDocumentContent(definition, formValues);
};

const DocumentGenerator = () => {
    const [selectedId, setSelectedId] = useState(DOCUMENT_DEFINITIONS[0].id);
    const selectedDefinition = useMemo(
        () => DOCUMENT_DEFINITIONS.find((item) => item.id === selectedId) ?? DOCUMENT_DEFINITIONS[0],
        [selectedId]
    );
    const [formValues, setFormValues] = useState<FormState>(defaultFormState(selectedDefinition));
    const [generationState, setGenerationState] = useState<GenerationState>({ status: 'idle' });

    const handleSelect = (id: string) => {
        setSelectedId(id);
        const nextDefinition = DOCUMENT_DEFINITIONS.find((item) => item.id === id);
        if (nextDefinition) {
            setFormValues(defaultFormState(nextDefinition));
            setGenerationState({ status: 'idle' });
        }
    };

    const handleChange = (field: DocumentField, value: string) => {
        setFormValues((prev) => ({ ...prev, [field.name]: value }));
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!selectedDefinition) return;
        setGenerationState({ status: 'loading' });
        try {
            const content = await generateDocument(selectedDefinition, formValues);
            setGenerationState({ status: 'done', content });
        } catch (error) {
            console.error(error);
            setGenerationState({ status: 'error', message: 'تعذر توليد المستند. يرجى المحاولة لاحقاً.' });
        }
    };

    const handleDownload = () => {
        if (generationState.status !== 'done' || !selectedDefinition) return;
        const pdfBlob = createPdf(selectedDefinition.name, generationState.content);
        const url = URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${selectedDefinition.name}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="grid gap-10 pb-24" dir="rtl">
            <section>
                <h1 className="mb-4 text-3xl font-bold sm:text-4xl">منصة إدارة وثائق الجمعيات</h1>
                <p className="max-w-3xl text-lg text-white/80">
                    صُممت هذه المنصة لتسريع إعداد الوثائق الإدارية والمالية الأساسية للجمعيات. اختَر نوع الوثيقة، عبّئ البيانات
                    المطلوبة، ودع الذكاء الاصطناعي يولّد لك محتوى احترافياً باللغة العربية قابل للتحميل بصيغة PDF.
                </p>
            </section>

            <section className="grid gap-6">
                <h2 className="text-2xl font-semibold">اختر نوع الوثيقة</h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {DOCUMENT_DEFINITIONS.map((definition) => {
                        const isActive = definition.id === selectedId;
                        return (
                            <button
                                key={definition.id}
                                type="button"
                                onClick={() => handleSelect(definition.id)}
                                className={`flex h-full flex-col items-start gap-2 rounded-xl border border-white/10 bg-white/5 p-5 text-right transition shadow-sm hover:border-primary/60 hover:bg-white/10 ${
                                    isActive ? 'border-primary/80 bg-primary/15' : ''
                                }`}
                            >
                                <span className="text-sm font-medium uppercase tracking-wide text-primary/90">{definition.name}</span>
                                <span className="text-base text-white/80">{definition.description}</span>
                            </button>
                        );
                    })}
                </div>
            </section>

            {selectedDefinition && (
                <section className="grid gap-6">
                    <div className="flex flex-col gap-2">
                        <h2 className="text-2xl font-semibold">معطيات الوثيقة</h2>
                        <p className="text-white/70">
                            الرجاء إدخال المعلومات المطلوبة أدناه. ستستخدم المنصة هذه المعطيات لتوليد نص مهني ومتناسق يعكس هوية الجمعية
                            ويلتزم بالمعايير الإدارية.
                        </p>
                    </div>
                    <form onSubmit={handleSubmit} className="grid gap-5 rounded-2xl border border-white/5 bg-white/5 p-6 shadow-lg">
                        {selectedDefinition.fields.map((field) => (
                            <label key={field.name} className="grid gap-2 text-right">
                                <span className="text-sm font-semibold text-white/90">
                                    {field.label}
                                    {field.required ? <span className="text-primary"> *</span> : null}
                                </span>
                                {field.type === 'textarea' ? (
                                    <textarea
                                        required={field.required}
                                        rows={field.rows ?? 4}
                                        value={formValues[field.name] ?? ''}
                                        onChange={(event) => handleChange(field, event.target.value)}
                                        placeholder={field.placeholder}
                                        className="w-full rounded-lg border border-white/10 bg-gray-900/70 px-3 py-2 text-white outline-none focus:border-primary"
                                    />
                                ) : (
                                    <input
                                        required={field.required}
                                        type={field.type}
                                        value={formValues[field.name] ?? ''}
                                        onChange={(event) => handleChange(field, event.target.value)}
                                        placeholder={field.placeholder}
                                        className="w-full rounded-lg border border-white/10 bg-gray-900/70 px-3 py-2 text-white outline-none focus:border-primary"
                                    />
                                )}
                                {field.helper && <span className="text-xs text-white/60">{field.helper}</span>}
                            </label>
                        ))}
                        <div className="flex flex-wrap justify-end gap-3 pt-2">
                            <button
                                type="submit"
                                className="btn"
                                disabled={generationState.status === 'loading'}
                            >
                                {generationState.status === 'loading' ? 'جاري التوليد...' : 'توليد الوثيقة'}
                            </button>
                        </div>
                    </form>
                </section>
            )}

            {generationState.status === 'done' && (
                <section className="grid gap-4 rounded-2xl border border-primary/50 bg-primary/10 p-6 shadow-lg">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <h2 className="text-2xl font-semibold">النص المولد</h2>
                        <div className="flex flex-wrap gap-3">
                            <button type="button" className="btn" onClick={handleDownload}>
                                تنزيل PDF
                            </button>
                            <button type="button" className="btn bg-white/10" onClick={() => setGenerationState({ status: 'idle' })}>
                                توليد وثيقة جديدة
                            </button>
                        </div>
                    </div>
                    <article className="whitespace-pre-line rounded-xl bg-gray-900/70 p-5 text-right leading-loose text-white/90">
                        {generationState.content}
                    </article>
                </section>
            )}

            {generationState.status === 'error' && (
                <section className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-right text-sm text-red-100">
                    {generationState.message}
                </section>
            )}
        </div>
    );
};

export default DocumentGenerator;
