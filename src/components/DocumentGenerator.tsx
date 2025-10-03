import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { createPdf } from '../lib/pdf';

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
    | { status: 'done'; content: string; metadata: { model: string; totalTokens: number | null } };

type HistoryEntry = {
    id: string;
    name: string;
    generatedAt: string;
    preview: string;
};

const DOCUMENT_DEFINITIONS: DocumentDefinition[] = [
    {
        id: 'annualActionPlan',
        name: 'خطة العمل السنوية',
        description: 'حدد الأهداف والأنشطة المبرمجة للسنة المقبلة مع مؤشرات التتبع.',
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
        description: 'أنشئ تقديراً مفصلاً للإيرادات والنفقات المتوقعة للسنة المالية.',
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

const truncate = (value: string, maxLength: number): string =>
    value.length <= maxLength ? value : `${value.slice(0, maxLength - 1).trim()}…`;

const DocumentGenerator = () => {
    const [selectedId, setSelectedId] = useState(DOCUMENT_DEFINITIONS[0].id);
    const selectedDefinition = useMemo(
        () => DOCUMENT_DEFINITIONS.find((item) => item.id === selectedId) ?? DOCUMENT_DEFINITIONS[0],
        [selectedId]
    );
    const [formValues, setFormValues] = useState<FormState>(defaultFormState(selectedDefinition));
    const [generationState, setGenerationState] = useState<GenerationState>({ status: 'idle' });
    const [history, setHistory] = useState<HistoryEntry[]>([]);
    const [copied, setCopied] = useState(false);
    const [showValidationErrors, setShowValidationErrors] = useState(false);
    const [downloadError, setDownloadError] = useState<string | null>(null);

    useEffect(() => {
        setFormValues(defaultFormState(selectedDefinition));
        setGenerationState({ status: 'idle' });
        setCopied(false);
        setShowValidationErrors(false);
        setDownloadError(null);
    }, [selectedDefinition]);

    const isFormValid = useMemo(
        () =>
            selectedDefinition.fields.every((field) => {
                if (!field.required) return true;
                const value = formValues[field.name];
                return typeof value === 'string' && value.trim().length > 0;
            }),
        [formValues, selectedDefinition]
    );

    const handleChange = (field: DocumentField, value: string) => {
        setFormValues((prev) => ({ ...prev, [field.name]: value }));
    };

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!selectedDefinition) return;
        if (!isFormValid) {
            setShowValidationErrors(true);
            return;
        }

        setGenerationState({ status: 'loading' });
        setCopied(false);
        setDownloadError(null);

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    documentType: {
                        id: selectedDefinition.id,
                        name: selectedDefinition.name,
                        description: selectedDefinition.description,
                        fields: selectedDefinition.fields.map((field) => ({
                            name: field.name,
                            label: field.label,
                            required: Boolean(field.required)
                        }))
                    },
                    values: formValues
                })
            });

            if (!response.ok) {
                const payload = await response.json().catch(() => null);
                const message = payload?.message ?? 'تعذر الاتصال بخدمة الذكاء الاصطناعي. يرجى المحاولة لاحقاً.';
                throw new Error(message);
            }

            const payload: { content?: string; model?: string; totalTokens?: number; usage?: { total_tokens?: number } } =
                await response.json();

            const content = payload.content?.trim();
            if (!content) {
                throw new Error('لم نتلق محتوى صالحاً من خدمة التوليد.');
            }

            const totalTokens = payload.totalTokens ?? payload.usage?.total_tokens ?? null;
            setGenerationState({
                status: 'done',
                content,
                metadata: {
                    model: payload.model ?? 'gpt-4o-mini',
                    totalTokens
                }
            });
            setHistory((prev) => [
                {
                    id: `${selectedDefinition.id}-${Date.now()}`,
                    name: selectedDefinition.name,
                    generatedAt: new Date().toISOString(),
                    preview: truncate(content, 140)
                },
                ...prev
            ].slice(0, 5));
        } catch (error) {
            const message = error instanceof Error ? error.message : 'حدث خطأ غير متوقع أثناء توليد الوثيقة.';
            setGenerationState({ status: 'error', message });
        }
    };

    const handleDownload = () => {
        if (generationState.status !== 'done' || !selectedDefinition) return;
        try {
            setDownloadError(null);
            const blob = createPdf(selectedDefinition.name, generationState.content);
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${selectedDefinition.name}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('PDF export error', error);
            setDownloadError('تعذر إنشاء ملف PDF. يرجى تحديث المتصفح أو إعادة المحاولة لاحقاً.');
        }
    };

    const handleCopy = async () => {
        if (generationState.status !== 'done') return;
        try {
            await navigator.clipboard.writeText(generationState.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Clipboard error', error);
        }
    };

    const getFieldError = (field: DocumentField): string | null => {
        if (!showValidationErrors || !field.required) return null;
        const value = formValues[field.name];
        if (!value || value.trim().length === 0) {
            return 'هذا الحقل مطلوب.';
        }
        return null;
    };

    return (
        <div className="grid gap-10 pb-24" dir="rtl">
            <section className="grid gap-3 text-right">
                <p className="text-sm uppercase tracking-[0.35em] text-white/60">منصة التسيير الذكي</p>
                <h1 className="text-3xl font-bold sm:text-4xl">توليد الوثائق الإدارية والمالية للجمعيات</h1>
                <p className="max-w-3xl text-lg text-white/80">
                    اختَر نوع الوثيقة، عبّئ التفاصيل الخاصة بجمعيتك، ثم دع الذكاء الاصطناعي يصوغ محتوى عربيّاً احترافياً قابلاً
                    للتنزيل بصيغة PDF في ثوانٍ معدودة.
                </p>
            </section>

            <div className="grid gap-8 xl:grid-cols-[minmax(0,320px)_1fr] xl:items-start">
                <aside className="grid gap-6">
                    <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-lg backdrop-blur">
                        <h2 className="mb-4 text-xl font-semibold text-white">الوثائق المتاحة</h2>
                        <div className="grid gap-3">
                            {DOCUMENT_DEFINITIONS.map((definition) => {
                                const isActive = definition.id === selectedDefinition.id;
                                return (
                                    <button
                                        key={definition.id}
                                        type="button"
                                        onClick={() => setSelectedId(definition.id)}
                                        className={`group flex flex-col gap-1 rounded-2xl border px-4 py-3 text-right transition ${
                                            isActive
                                                ? 'border-primary/80 bg-primary/20 text-white shadow-lg'
                                                : 'border-white/10 bg-white/0 text-white/80 hover:border-primary/60 hover:bg-white/5'
                                        }`}
                                    >
                                        <span className="text-base font-semibold">{definition.name}</span>
                                        <span className="text-sm text-white/70 group-hover:text-white/80">
                                            {definition.description}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </section>

                    {history.length > 0 && (
                        <section className="rounded-3xl border border-white/5 bg-white/5 p-6 shadow-lg backdrop-blur">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-white">أحدث الوثائق</h2>
                                <span className="text-xs text-white/60">آخر {history.length} عملية توليد</span>
                            </div>
                            <ul className="mt-4 grid gap-3 text-sm text-white/75">
                                {history.map((entry) => (
                                    <li key={entry.id} className="rounded-2xl border border-white/5 bg-white/5 p-3">
                                        <p className="font-semibold text-white/90">{entry.name}</p>
                                        <p className="text-xs text-white/60">
                                            {new Date(entry.generatedAt).toLocaleString('ar-MA', {
                                                hour: '2-digit',
                                                minute: '2-digit',
                                                day: '2-digit',
                                                month: '2-digit'
                                            })}
                                        </p>
                                        <p className="mt-1 text-white/70">{entry.preview}</p>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}
                </aside>

                <section className="grid gap-6">
                    <form onSubmit={handleSubmit} className="grid gap-5 rounded-3xl border border-white/10 bg-white/10 p-6 shadow-xl">
                        <div className="flex flex-col gap-1 text-right">
                            <h2 className="text-2xl font-semibold text-white">معطيات الوثيقة</h2>
                            <p className="text-sm text-white/70">
                                أدخل المعطيات المطلوبة بدقة. سيتم تضمين كل حقل في المسودة النهائية مع الحفاظ على سياق إداري ولغوي
                                متناسق.
                            </p>
                        </div>

                        <div className="grid gap-4">
                            {selectedDefinition.fields.map((field) => {
                                const error = getFieldError(field);
                                return (
                                    <label key={field.name} className="grid gap-2 text-right">
                                        <span className="text-sm font-semibold text-white">
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
                                                className={`w-full rounded-2xl border bg-gray-950/50 px-3 py-2 text-base text-white shadow-inner outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/40 ${
                                                    error ? 'border-red-400/70 focus:ring-red-400/60' : 'border-white/10'
                                                }`}
                                                aria-invalid={Boolean(error)}
                                            />
                                        ) : (
                                            <input
                                                required={field.required}
                                                type={field.type}
                                                value={formValues[field.name] ?? ''}
                                                onChange={(event) => handleChange(field, event.target.value)}
                                                placeholder={field.placeholder}
                                                className={`w-full rounded-2xl border bg-gray-950/50 px-3 py-2 text-base text-white shadow-inner outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/40 ${
                                                    error ? 'border-red-400/70 focus:ring-red-400/60' : 'border-white/10'
                                                }`}
                                                aria-invalid={Boolean(error)}
                                            />
                                        )}
                                        {field.helper && <span className="text-xs text-white/60">{field.helper}</span>}
                                        {error && <span className="text-xs text-red-200">{error}</span>}
                                    </label>
                                );
                            })}
                        </div>

                        <div className="flex flex-wrap justify-end gap-3 pt-2">
                            <button
                                type="submit"
                                className="btn btn-lg"
                                disabled={generationState.status === 'loading'}
                            >
                                {generationState.status === 'loading' ? 'جاري توليد الوثيقة…' : 'توليد الوثيقة الآن'}
                            </button>
                            <button
                                type="button"
                                className="btn btn-lg bg-white/10 text-white"
                                onClick={() => {
                                    setFormValues(defaultFormState(selectedDefinition));
                                    setShowValidationErrors(false);
                                    setGenerationState({ status: 'idle' });
                                    setCopied(false);
                                    setDownloadError(null);
                                }}
                            >
                                إعادة تعيين الحقول
                            </button>
                        </div>
                    </form>

                    {generationState.status === 'loading' && (
                        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 text-right text-white/80 shadow-lg">
                            <p className="font-medium">نقوم بتحليل المعطيات وصياغة الوثيقة…</p>
                            <p className="mt-2 text-sm text-white/60">
                                تستغرق العملية بضع ثوانٍ حسب طول المعلومات التي تم إدخالها.
                            </p>
                        </section>
                    )}

                    {generationState.status === 'error' && (
                        <section className="rounded-3xl border border-red-400/40 bg-red-500/10 p-6 text-right text-red-100 shadow-lg">
                            <h2 className="text-xl font-semibold text-red-200">تعذر توليد الوثيقة</h2>
                            <p className="mt-2 text-sm leading-7">{generationState.message}</p>
                        </section>
                    )}

                    {generationState.status === 'done' && (
                        <section className="grid gap-4 rounded-3xl border border-primary/60 bg-primary/15 p-6 text-right text-white shadow-xl">
                            <header className="flex flex-wrap items-center justify-between gap-4">
                                <div>
                                    <h2 className="text-2xl font-semibold">النص المولد</h2>
                                    <p className="text-sm text-white/70">
                                        {generationState.metadata.totalTokens
                                            ? `تم التوليد باستعمال النموذج ${generationState.metadata.model} (${generationState.metadata.totalTokens} وحدة معالجة).`
                                            : `تم التوليد باستعمال النموذج ${generationState.metadata.model}.`}
                                    </p>
                                </div>
                                <div className="flex flex-wrap gap-3">
                                    <button type="button" className="btn" onClick={handleDownload}>
                                        تنزيل PDF
                                    </button>
                                    <button type="button" className="btn bg-white/10 text-white" onClick={handleCopy}>
                                        {copied ? 'تم النسخ ✔' : 'نسخ المحتوى'}
                                    </button>
                                </div>
                                {downloadError && (
                                    <p className="mt-2 text-sm text-red-200">{downloadError}</p>
                                )}
                            </header>
                            <article className="max-h-[480px] overflow-y-auto whitespace-pre-wrap rounded-2xl bg-gray-950/40 p-5 leading-8 text-white/95 shadow-inner">
                                {generationState.content}
                            </article>
                            <div className="flex justify-end">
                                <button
                                    type="button"
                                    className="btn bg-white/10 text-white"
                                    onClick={() => {
                                        setGenerationState({ status: 'idle' });
                                        setDownloadError(null);
                                    }}
                                >
                                    توليد وثيقة جديدة
                                </button>
                            </div>
                        </section>
                    )}
                </section>
            </div>
        </div>
    );
};

export default DocumentGenerator;
