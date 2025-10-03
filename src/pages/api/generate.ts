import type { APIRoute } from 'astro';

export const prerender = false;

const API_URL = 'https://api.openai.com/v1/chat/completions';
const API_KEY =
    import.meta.env.DOCUMENT_AUTOMATION_OPENAI_KEY ??
    import.meta.env.OPENAI_API_KEY ??
    process.env.DOCUMENT_AUTOMATION_OPENAI_KEY ??
    process.env.OPENAI_API_KEY ??
    '';

const buildUserPrompt = (
    documentType: {
        id: string;
        name: string;
        description: string;
        fields: { name: string; label: string; required: boolean }[];
    },
    values: Record<string, string>
): string => {
    const formattedFields = documentType.fields
        .map((field) => {
            const value = values[field.name]?.trim();
            return `- ${field.label}: ${value && value.length > 0 ? value : 'غير محدد'}`;
        })
        .join('\n');

    return `أرغب في إعداد وثيقة مهنية بعنوان "${documentType.name}" وفقاً للوصف التالي: ${documentType.description}.

المعطيات التفصيلية التي يجب الاعتماد عليها:
${formattedFields}

التعليمات:
- صغ المحتوى باللغة العربية الفصحى مع الحفاظ على أسلوب مهني واضح ومتماسك.
- قدم النص في فقرات أو فصول منظمة بعناوين فرعية عند الحاجة.
- تأكد من إدراج الأرقام والتواريخ والأسماء كما هي دون ترجمة أو تعديل.
- أضف خاتمة مختصرة توضح الخطوات التالية أو التوصيات حسب نوع الوثيقة.
- اجعل طول النص مناسباً لطبيعة الوثيقة دون حشو أو تكرار.`;
};

export const POST: APIRoute = async ({ request }) => {
    if (!API_KEY) {
        return new Response(JSON.stringify({ message: 'لم يتم ضبط مفتاح واجهة البرمجة الخاصة بالذكاء الاصطناعي.' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    try {
        const body = (await request.json()) as {
            documentType?: { id: string; name: string; description: string; fields: { name: string; label: string; required: boolean }[] };
            values?: Record<string, string>;
        };

        if (!body.documentType || !body.values) {
            return new Response(JSON.stringify({ message: 'المعطيات المرسلة غير مكتملة.' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const userPrompt = buildUserPrompt(body.documentType, body.values);

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${API_KEY}`
            },
            body: JSON.stringify({
                model: 'gpt-4o-mini',
                temperature: 0.4,
                messages: [
                    {
                        role: 'system',
                        content:
                            'أنت مساعد خبير في إعداد وثائق الجمعيات. جميع المخرجات يجب أن تكون باللغة العربية الفصحى بأسلوب إداري منظم ومهني.'
                    },
                    { role: 'user', content: userPrompt }
                ]
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => null);
            const message = error?.error?.message ?? 'فشل الاتصال بخدمة الذكاء الاصطناعي.';
            return new Response(JSON.stringify({ message }), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const payload = await response.json();
        const choice = payload.choices?.[0]?.message?.content?.trim();

        if (!choice) {
            return new Response(JSON.stringify({ message: 'لم يتم تلقي أي محتوى من خدمة الذكاء الاصطناعي.' }), {
                status: 502,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        return new Response(
            JSON.stringify({
                content: choice,
                model: payload.model ?? 'gpt-4o-mini',
                totalTokens: payload.usage?.total_tokens ?? null
            }),
            {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    } catch (error) {
        console.error('AI generation error', error);
        return new Response(JSON.stringify({ message: 'وقع خطأ غير متوقع أثناء توليد الوثيقة.' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
};
