import { useMemo, useState } from 'react';

type DiscountType = 'percent' | 'amount';

type Product = {
    id: string;
    name: string;
    category: string;
    price: number;
    icon: string;
    accent: string;
    tags: string[];
    stockStatus: 'inStock' | 'lowStock' | 'outOfStock';
    pairings?: string[];
};

type CartLine = {
    productId: string;
    quantity: number;
    note: string;
};

type CartItem = Product & {
    quantity: number;
    note: string;
    lineTotal: number;
};

type HoldOrder = {
    id: string;
    label: string;
    cart: CartLine[];
    createdAt: string;
    customerName: string;
    orderNotes: string;
    discount: number;
    discountType: DiscountType;
    serviceFee: number;
    redeemLoyalty: boolean;
    paymentMethod: PaymentMethod;
    estimatedTotal: number;
};

type PaymentMethod = 'cash' | 'card' | 'mobile' | 'split';

type SalesMetrics = {
    turnover: number;
    tickets: number;
    items: number;
    loyaltyUsed: number;
};

const MAD = new Intl.NumberFormat('ar-MA', {
    style: 'currency',
    currency: 'MAD',
    minimumFractionDigits: 2
});

const TAX_RATE = 0.09;

const PAYMENT_METHODS: { id: PaymentMethod; label: string; description: string }[] = [
    { id: 'cash', label: 'نقداً', description: 'تحصيل فوري مع إمكانية إعطاء باقي المبلغ.' },
    { id: 'card', label: 'بطاقة بنكية', description: 'دفع عبر بطاقة بنكية مع مزامنة تلقائية للمحاسبة.' },
    { id: 'mobile', label: 'محفظة رقمية', description: 'دفع عبر التطبيقات البنكية و QR Code.' },
    { id: 'split', label: 'دفع مقسّم', description: 'توزيع المبلغ بين أكثر من وسيلة دفع.' }
];

const PRODUCTS: Product[] = [
    {
        id: 'espresso',
        name: 'إسبريسو فاخر',
        category: 'مشروبات ساخنة',
        price: 24,
        icon: '☕️',
        accent: 'from-orange-400 to-amber-500',
        tags: ['مبيع-سريع', 'صباحي'],
        stockStatus: 'inStock',
        pairings: ['كوكيز الشوفان', 'ميني كرواسان']
    },
    {
        id: 'flatWhite',
        name: 'فلات وايت',
        category: 'مشروبات ساخنة',
        price: 29,
        icon: '🥛',
        accent: 'from-teal-400 to-emerald-500',
        tags: ['مميز', 'حليب-عضوي'],
        stockStatus: 'lowStock',
        pairings: ['كيك الفستق']
    },
    {
        id: 'coldBrew',
        name: 'كولد برو بالكاراميل',
        category: 'مشروبات باردة',
        price: 32,
        icon: '🧊',
        accent: 'from-sky-400 to-blue-500',
        tags: ['موسمي', 'بارد'],
        stockStatus: 'inStock',
        pairings: ['تشيزكيك التوت']
    },
    {
        id: 'matcha',
        name: 'ماتشا لاتيه',
        category: 'مشروبات باردة',
        price: 34,
        icon: '🍵',
        accent: 'from-lime-400 to-emerald-500',
        tags: ['نباتي', 'بدون-سكر'],
        stockStatus: 'inStock',
        pairings: ['كوكيز الشوفان']
    },
    {
        id: 'saltedCaramel',
        name: 'كراميل مملح',
        category: 'مشروبات باردة',
        price: 28,
        icon: '🍯',
        accent: 'from-amber-400 to-orange-500',
        tags: ['مبيع-سريع'],
        stockStatus: 'inStock',
        pairings: ['براونيز الشوكولاتة الداكنة']
    },
    {
        id: 'acaiBowl',
        name: 'وعاء آساي طاقة',
        category: 'أطعمة خفيفة',
        price: 42,
        icon: '🥣',
        accent: 'from-purple-400 to-fuchsia-500',
        tags: ['صحي', 'موسمي'],
        stockStatus: 'inStock',
        pairings: ['عصير أخضر']
    },
    {
        id: 'avocadoToast',
        name: 'توست أفوكادو',
        category: 'أطعمة خفيفة',
        price: 36,
        icon: '🥑',
        accent: 'from-emerald-400 to-teal-500',
        tags: ['نباتي', 'مبيع-سريع'],
        stockStatus: 'lowStock',
        pairings: ['عصير الحمضيات المنعش']
    },
    {
        id: 'brownie',
        name: 'براونيز داكن',
        category: 'حلويات',
        price: 26,
        icon: '🍫',
        accent: 'from-rose-400 to-pink-500',
        tags: ['خالي-من-الجلوتين'],
        stockStatus: 'inStock',
        pairings: ['إسبريسو فاخر']
    },
    {
        id: 'cheesecake',
        name: 'تشيزكيك التوت الأزرق',
        category: 'حلويات',
        price: 38,
        icon: '🫐',
        accent: 'from-indigo-400 to-violet-500',
        tags: ['مميز'],
        stockStatus: 'inStock',
        pairings: ['كولد برو بالكاراميل']
    },
    {
        id: 'proteinShake',
        name: 'مشروب بروتين الشوفان',
        category: 'مشروبات صحية',
        price: 33,
        icon: '💪',
        accent: 'from-amber-400 to-lime-500',
        tags: ['رياضي', 'عالي-البروتين'],
        stockStatus: 'inStock',
        pairings: ['توست أفوكادو']
    },
    {
        id: 'greenJuice',
        name: 'عصير أخضر منعش',
        category: 'مشروبات صحية',
        price: 27,
        icon: '🥬',
        accent: 'from-emerald-400 to-green-500',
        tags: ['ديتوكس'],
        stockStatus: 'inStock',
        pairings: ['وعاء آساي طاقة']
    },
    {
        id: 'kidsCombo',
        name: 'عرض الأطفال المرح',
        category: 'عروض خاصة',
        price: 31,
        icon: '🧃',
        accent: 'from-pink-400 to-orange-500',
        tags: ['عائلي', 'عرض-اليوم'],
        stockStatus: 'inStock',
        pairings: ['براونيز داكن']
    }
];

const QUICK_DISCOUNTS: { label: string; type: DiscountType; value: number }[] = [
    { label: 'خصم 5%', type: 'percent', value: 5 },
    { label: 'خصم 10%', type: 'percent', value: 10 },
    { label: 'خصم 20 درهم', type: 'amount', value: 20 }
];

const formatCurrency = (value: number): string => MAD.format(Math.max(value, 0));

const formatDateTime = (value: Date): string =>
    new Intl.DateTimeFormat('ar-MA', { dateStyle: 'medium', timeStyle: 'short' }).format(value);

const sumLineItems = (cart: CartLine[]): number =>
    cart.reduce((total, line) => {
        const product = PRODUCTS.find((item) => item.id === line.productId);
        if (!product) return total;
        return total + product.price * line.quantity;
    }, 0);

const PosSystem = (): JSX.Element => {
    const [cart, setCart] = useState<CartLine[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string>('الكل');
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [discount, setDiscount] = useState<number>(0);
    const [discountType, setDiscountType] = useState<DiscountType>('percent');
    const [serviceFee, setServiceFee] = useState<number>(0);
    const [redeemLoyalty, setRedeemLoyalty] = useState<boolean>(false);
    const [customerName, setCustomerName] = useState<string>('زبون عابر');
    const [orderNotes, setOrderNotes] = useState<string>('');
    const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('card');
    const [heldOrders, setHeldOrders] = useState<HoldOrder[]>([]);
    const [nextOrderNumber, setNextOrderNumber] = useState<number>(3721);
    const [statusMessage, setStatusMessage] = useState<string>('جاهز لاستقبال الطلبات');
    const [recentReceipt, setRecentReceipt] = useState<string | null>(null);
    const [salesMetrics, setSalesMetrics] = useState<SalesMetrics>({
        turnover: 12850,
        tickets: 38,
        items: 152,
        loyaltyUsed: 184
    });
    const [loyaltyPoints, setLoyaltyPoints] = useState<number>(420);

    const categories = useMemo(() => ['الكل', ...new Set(PRODUCTS.map((product) => product.category))], []);

    const filteredProducts = useMemo(() => {
        const term = searchTerm.trim().toLowerCase();
        return PRODUCTS.filter((product) => {
            const matchesCategory = selectedCategory === 'الكل' || product.category === selectedCategory;
            const matchesTerm =
                term.length === 0 ||
                product.name.toLowerCase().includes(term) ||
                product.tags.some((tag) => tag.toLowerCase().includes(term));
            return matchesCategory && matchesTerm;
        });
    }, [selectedCategory, searchTerm]);

    const cartWithDetails = useMemo<CartItem[]>(() => {
        return cart
            .map((line) => {
                const product = PRODUCTS.find((item) => item.id === line.productId);
                if (!product) return null;
                const lineTotal = product.price * line.quantity;
                return { ...product, quantity: line.quantity, note: line.note, lineTotal } as CartItem;
            })
            .filter((item): item is CartItem => item !== null);
    }, [cart]);

    const subtotal = useMemo(() => sumLineItems(cart), [cart]);

    const appliedDiscount = useMemo(() => {
        if (discountType === 'percent') {
            return Math.min((subtotal * discount) / 100, subtotal);
        }
        return Math.min(discount, subtotal);
    }, [discount, discountType, subtotal]);

    const taxableBase = Math.max(subtotal - appliedDiscount, 0);
    const taxAmount = taxableBase * TAX_RATE;
    const potentialTotal = taxableBase + taxAmount + serviceFee;
    const loyaltyRedeemValue = redeemLoyalty ? Math.min(loyaltyPoints * 0.1, potentialTotal) : 0;
    const totalDue = Math.max(potentialTotal - loyaltyRedeemValue, 0);

    const totalItems = useMemo(
        () => cart.reduce((sum, line) => sum + line.quantity, 0),
        [cart]
    );

    const topCategory = useMemo(() => {
        const counts = new Map<string, number>();
        cart.forEach((line) => {
            const product = PRODUCTS.find((item) => item.id === line.productId);
            if (!product) return;
            counts.set(product.category, (counts.get(product.category) ?? 0) + line.quantity);
        });
        let popularCategory = '';
        let max = 0;
        counts.forEach((value, key) => {
            if (value > max) {
                popularCategory = key;
                max = value;
            }
        });
        return popularCategory || 'مشروبات ساخنة';
    }, [cart]);

    const suggestions = useMemo(() => {
        const preferredCategory = topCategory;
        const currentIds = new Set(cart.map((line) => line.productId));
        return PRODUCTS.filter(
            (product) =>
                product.category === preferredCategory &&
                !currentIds.has(product.id) &&
                product.stockStatus !== 'outOfStock'
        ).slice(0, 3);
    }, [cart, topCategory]);

    const handleAddProduct = (productId: string) => {
        const product = PRODUCTS.find((item) => item.id === productId);
        if (!product || product.stockStatus === 'outOfStock') return;
        setCart((prev) => {
            const existing = prev.find((line) => line.productId === productId);
            if (existing) {
                return prev.map((line) =>
                    line.productId === productId
                        ? { ...line, quantity: Math.min(line.quantity + 1, 99) }
                        : line
                );
            }
            return [...prev, { productId, quantity: 1, note: '' }];
        });
        setStatusMessage(`تمت إضافة ${product.name} إلى الطلب.`);
    };

    const handleUpdateQuantity = (productId: string, quantity: number) => {
        if (quantity <= 0) {
            handleRemoveLine(productId);
            return;
        }
        setCart((prev) =>
            prev.map((line) => (line.productId === productId ? { ...line, quantity } : line))
        );
    };

    const handleRemoveLine = (productId: string) => {
        setCart((prev) => prev.filter((line) => line.productId !== productId));
    };

    const handleNoteChange = (productId: string, note: string) => {
        setCart((prev) =>
            prev.map((line) => (line.productId === productId ? { ...line, note } : line))
        );
    };

    const handleApplyQuickDiscount = (value: number, type: DiscountType) => {
        setDiscountType(type);
        setDiscount(value);
    };

    const handleHoldOrder = () => {
        if (cart.length === 0) {
            setStatusMessage('لا يمكن تعليق طلب فارغ.');
            return;
        }
        const estimatedTotal = potentialTotal;
        const hold: HoldOrder = {
            id: `HLD-${Date.now()}`,
            label: `طلب معلق ${heldOrders.length + 1}`,
            cart: cart.map((line) => ({ ...line })),
            createdAt: new Date().toISOString(),
            customerName,
            orderNotes,
            discount,
            discountType,
            serviceFee,
            redeemLoyalty,
            paymentMethod,
            estimatedTotal
        };
        setHeldOrders((prev) => [...prev, hold]);
        setCart([]);
        setDiscount(0);
        setRedeemLoyalty(false);
        setServiceFee(0);
        setOrderNotes('');
        setStatusMessage(`تم تعليق ${hold.label}. يمكنك استرجاعه لاحقاً.`);
    };

    const handleResumeOrder = (orderId: string) => {
        const hold = heldOrders.find((item) => item.id === orderId);
        if (!hold) return;
        setCart(hold.cart.map((line) => ({ ...line })));
        setCustomerName(hold.customerName);
        setOrderNotes(hold.orderNotes);
        setDiscount(hold.discount);
        setDiscountType(hold.discountType);
        setServiceFee(hold.serviceFee);
        setRedeemLoyalty(hold.redeemLoyalty);
        setPaymentMethod(hold.paymentMethod);
        setHeldOrders((prev) => prev.filter((item) => item.id !== orderId));
        setStatusMessage(`تم استرجاع ${hold.label} بنجاح.`);
    };

    const handleCompleteOrder = () => {
        if (cart.length === 0) {
            setStatusMessage('أضف منتجات إلى السلة قبل إتمام الطلب.');
            return;
        }
        const now = new Date();
        const orderId = nextOrderNumber;
        const receiptLines: (string | null)[] = [
            'مقهى فيوجن - منصة نقاط البيع الذكية',
            `فاتورة رقم ${orderId}`,
            `التاريخ: ${formatDateTime(now)}`,
            `أمين الصندوق: سلمى بناني`,
            customerName ? `الزبون: ${customerName}` : null,
            '',
            'تفاصيل الطلب:'
        ];

        cartWithDetails.forEach((item) => {
            receiptLines.push(`${item.name} x${item.quantity} — ${formatCurrency(item.lineTotal)}`);
            if (item.note) {
                receiptLines.push(`  • ملاحظة: ${item.note}`);
            }
        });

        receiptLines.push('', `المجموع الفرعي: ${formatCurrency(subtotal)}`);
        receiptLines.push(`الخصم: -${formatCurrency(appliedDiscount)}`);
        receiptLines.push(`الضريبة (${Math.round(TAX_RATE * 100)}%): ${formatCurrency(taxAmount)}`);
        receiptLines.push(`رسوم الخدمة: ${formatCurrency(serviceFee)}`);
        if (loyaltyRedeemValue > 0) {
            receiptLines.push(`النقاط المستخدمة: -${formatCurrency(loyaltyRedeemValue)}`);
        }
        receiptLines.push(`الإجمالي المستحق: ${formatCurrency(totalDue)}`);
        receiptLines.push(`طريقة الدفع: ${PAYMENT_METHODS.find((m) => m.id === paymentMethod)?.label ?? ''}`);
        if (orderNotes) {
            receiptLines.push('', `ملاحظات إضافية: ${orderNotes}`);
        }
        receiptLines.push('', 'شكراً لزيارتكم ونتمنى لكم يوماً جميلاً!');

        setRecentReceipt(receiptLines.filter(Boolean).join('\n'));
        setStatusMessage(`تم إتمام الطلب #${orderId} بنجاح.`);
        setNextOrderNumber((prev) => prev + 1);
        const redeemedPoints = Math.round(loyaltyRedeemValue / 0.1);
        const earnedPoints = Math.round(totalDue / 10);
        setLoyaltyPoints((prev) => Math.max(prev - redeemedPoints + earnedPoints, 0));
        setSalesMetrics((prev) => ({
            turnover: prev.turnover + totalDue,
            tickets: prev.tickets + 1,
            items: prev.items + totalItems,
            loyaltyUsed: prev.loyaltyUsed + loyaltyRedeemValue
        }));
        setCart([]);
        setDiscount(0);
        setServiceFee(0);
        setRedeemLoyalty(false);
        setOrderNotes('');
    };

    const handleReset = () => {
        setCart([]);
        setDiscount(0);
        setRedeemLoyalty(false);
        setServiceFee(0);
        setOrderNotes('');
        setStatusMessage('تمت تهيئة الشاشة لطلب جديد.');
    };

    return (
        <div className="space-y-8">
            <header className="flex flex-col gap-6 bg-white/5 border border-white/10 rounded-3xl p-6 shadow-xl shadow-black/20 sm:flex-row sm:items-center sm:justify-between">
                <div className="space-y-2">
                    <p className="text-sm text-white/60">{formatDateTime(new Date())}</p>
                    <h1 className="text-3xl font-semibold">نظام نقاط البيع المتطور</h1>
                    <p className="text-white/70">
                        إدارة لحظية للمبيعات، المخزون، وبرامج الولاء من واجهة واحدة موجهة للفريق الأمامي.
                    </p>
                </div>
                <div className="flex flex-col gap-4 sm:w-64">
                    <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white/80">
                        <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">حالة المنصة</span>
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-3 py-1 text-emerald-200 text-xs">
                                <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" /> نشطة
                            </span>
                        </div>
                        <p className="mt-2 leading-relaxed text-white/70">{statusMessage}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs text-white/70">
                        <div className="rounded-2xl border border-white/5 bg-white/5 px-3 py-3">
                            <p className="text-white/50">مبيعات اليوم</p>
                            <p className="mt-1 text-lg font-semibold text-white">{formatCurrency(salesMetrics.turnover)}</p>
                        </div>
                        <div className="rounded-2xl border border-white/5 bg-white/5 px-3 py-3">
                            <p className="text-white/50">متوسط السلة</p>
                            <p className="mt-1 text-lg font-semibold text-white">
                                {salesMetrics.tickets > 0 ? formatCurrency(salesMetrics.turnover / salesMetrics.tickets) : formatCurrency(0)}
                            </p>
                        </div>
                        <div className="rounded-2xl border border-white/5 bg-white/5 px-3 py-3">
                            <p className="text-white/50">عدد التذاكر</p>
                            <p className="mt-1 text-lg font-semibold text-white">{salesMetrics.tickets}</p>
                        </div>
                        <div className="rounded-2xl border border-white/5 bg-white/5 px-3 py-3">
                            <p className="text-white/50">نقاط مستخدمة</p>
                            <p className="mt-1 text-lg font-semibold text-white">{formatCurrency(salesMetrics.loyaltyUsed)}</p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="grid gap-6 xl:grid-cols-[1.7fr_1fr]">
                <section className="space-y-6">
                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                            <div>
                                <h2 className="text-2xl font-semibold">قائمة المنتجات الذكية</h2>
                                <p className="mt-1 text-sm text-white/70">
                                    تصفية ديناميكية مع إظهار حالة المخزون والاقتراحات حسب الطلب الحالي.
                                </p>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-white/70">
                                <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2">
                                    <span className="h-2 w-2 rounded-full bg-emerald-300" /> مخزون مستقر
                                </span>
                                <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2">
                                    <span className="h-2 w-2 rounded-full bg-amber-300" /> منتجات محدودة
                                </span>
                            </div>
                        </div>

                        <div className="mt-6 grid gap-4 lg:grid-cols-[1.3fr_auto]">
                            <div className="relative">
                                <input
                                    type="search"
                                    value={searchTerm}
                                    onChange={(event) => setSearchTerm(event.target.value)}
                                    placeholder="ابحث عن منتج، مكوّن، أو وسم..."
                                    className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-white/50 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/40"
                                />
                                <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-white/40">
                                    🔍
                                </span>
                            </div>
                            <div className="flex items-center gap-2 overflow-x-auto pb-1">
                                {categories.map((category) => (
                                    <button
                                        key={category}
                                        type="button"
                                        onClick={() => setSelectedCategory(category)}
                                        className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-medium transition ${
                                            selectedCategory === category
                                                ? 'bg-primary text-primary-content shadow-lg shadow-primary/30'
                                                : 'bg-white/10 text-white/70 hover:bg-white/20'
                                        }`}
                                    >
                                        {category}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mt-6 grid gap-4 sm:grid-cols-2 2xl:grid-cols-3">
                            {filteredProducts.map((product) => (
                                <article
                                    key={product.id}
                                    className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-4 transition hover:-translate-y-0.5 hover:border-primary/60 hover:shadow-2xl hover:shadow-primary/20"
                                >
                                    <div
                                        className={`absolute -right-12 -top-12 h-28 w-28 rotate-45 bg-gradient-to-br opacity-20 ${product.accent}`}
                                    />
                                    <div className="relative flex items-start justify-between">
                                        <div className="flex flex-col gap-2">
                                            <span className="text-3xl" aria-hidden>
                                                {product.icon}
                                            </span>
                                            <h3 className="text-lg font-semibold">{product.name}</h3>
                                            <p className="text-sm text-white/60">{product.category}</p>
                                            <p className="text-base font-semibold text-primary/90">
                                                {formatCurrency(product.price)}
                                            </p>
                                        </div>
                                        <div className="flex flex-col items-end gap-2 text-xs">
                                            <span
                                                className={`rounded-full px-3 py-1 font-medium ${
                                                    product.stockStatus === 'inStock'
                                                        ? 'bg-emerald-500/15 text-emerald-200'
                                                        : product.stockStatus === 'lowStock'
                                                        ? 'bg-amber-500/20 text-amber-200'
                                                        : 'bg-rose-500/20 text-rose-200'
                                                }`}
                                            >
                                                {product.stockStatus === 'inStock'
                                                    ? 'متوفر'
                                                    : product.stockStatus === 'lowStock'
                                                    ? 'كَمِية محدودة'
                                                    : 'غير متاح'}
                                            </span>
                                            <div className="flex flex-wrap justify-end gap-2">
                                                {product.tags.map((tag) => (
                                                    <span
                                                        key={tag}
                                                        className="rounded-full bg-white/10 px-3 py-1 text-[11px] text-white/60"
                                                    >
                                                        #{tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                    {product.pairings && (
                                        <p className="mt-4 text-xs text-white/60">
                                            اقتراح تقديم: {product.pairings.join(' + ')}
                                        </p>
                                    )}
                                    <button
                                        type="button"
                                        disabled={product.stockStatus === 'outOfStock'}
                                        onClick={() => handleAddProduct(product.id)}
                                        className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-primary py-2 text-sm font-semibold text-primary-content transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/40"
                                    >
                                        أضف إلى الطلب
                                    </button>
                                </article>
                            ))}
                            {filteredProducts.length === 0 && (
                                <div className="col-span-full flex flex-col items-center justify-center rounded-3xl border border-dashed border-white/20 bg-white/5 p-10 text-center text-sm text-white/60">
                                    <span className="text-3xl">🧭</span>
                                    <p className="mt-4 font-medium text-white">لا توجد نتائج مطابقة</p>
                                    <p className="mt-2">عدّل معايير البحث أو استكشف فئات أخرى.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">اقتراحات ذكية</h2>
                            <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/60">
                                فئة مفضلة: {topCategory}
                            </span>
                        </div>
                        <p className="mt-1 text-sm text-white/70">
                            يتم تحديث هذه الاقتراحات تلقائياً حسب أصناف السلة الحالية وسلوكيات البيع.
                        </p>
                        <div className="mt-4 grid gap-4 sm:grid-cols-3">
                            {suggestions.map((product) => (
                                <button
                                    key={product.id}
                                    type="button"
                                    onClick={() => handleAddProduct(product.id)}
                                    className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left text-sm transition hover:border-primary/70 hover:bg-primary/10"
                                >
                                    <p className="text-lg">{product.icon}</p>
                                    <p className="mt-2 font-semibold text-white">{product.name}</p>
                                    <p className="text-xs text-white/60">{formatCurrency(product.price)}</p>
                                </button>
                            ))}
                            {suggestions.length === 0 && (
                                <p className="col-span-full rounded-2xl border border-dashed border-white/20 bg-white/5 p-6 text-center text-sm text-white/60">
                                    أضف منتجات إلى السلة للحصول على توصيات مخصصة.
                                </p>
                            )}
                        </div>
                    </div>
                </section>

                <section className="space-y-6">
                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                                <h2 className="text-2xl font-semibold">ملخص الطلب الحالي</h2>
                                <p className="text-sm text-white/60">إدارة تفاصيل الطلب، الملاحظات، والخصومات من هنا.</p>
                            </div>
                            <div className="text-sm text-white/50">رقم الطلب التالي: #{nextOrderNumber}</div>
                        </div>

                        <div className="mt-4 space-y-4">
                            {cartWithDetails.length === 0 ? (
                                <div className="rounded-2xl border border-dashed border-white/15 bg-white/5 p-10 text-center text-sm text-white/60">
                                    <p className="text-lg font-semibold text-white">السلة فارغة حالياً</p>
                                    <p className="mt-2">ابدأ بإضافة منتجات من القائمة لعرض تفاصيل الطلب.</p>
                                </div>
                            ) : (
                                cartWithDetails.map((item) => (
                                    <div
                                        key={item.id}
                                        className="rounded-2xl border border-white/10 bg-white/5 p-4"
                                    >
                                        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                                            <div>
                                                <p className="text-lg font-semibold">{item.name}</p>
                                                <p className="text-sm text-white/60">{item.category}</p>
                                                <p className="mt-2 text-sm text-white/60">
                                                    {item.pairings ? `يقترح مع: ${item.pairings.join(' + ')}` : 'خيار مستقل'}
                                                </p>
                                            </div>
                                            <div className="flex flex-col items-end gap-3">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        type="button"
                                                        onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                                                        className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-lg text-white/70 transition hover:bg-white/20"
                                                    >
                                                        −
                                                    </button>
                                                    <span className="min-w-[2ch] text-center font-semibold">
                                                        {item.quantity}
                                                    </span>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleUpdateQuantity(item.id, Math.min(item.quantity + 1, 99))}
                                                        className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-lg text-white/70 transition hover:bg-white/20"
                                                    >
                                                        +
                                                    </button>
                                                </div>
                                                <p className="text-sm font-semibold text-primary/90">
                                                    {formatCurrency(item.lineTotal)}
                                                </p>
                                                <button
                                                    type="button"
                                                    onClick={() => handleRemoveLine(item.id)}
                                                    className="text-xs text-rose-300 hover:text-rose-200"
                                                >
                                                    إزالة من السلة
                                                </button>
                                            </div>
                                        </div>
                                        <textarea
                                            value={item.note}
                                            onChange={(event) => handleNoteChange(item.id, event.target.value)}
                                            placeholder="أضف ملاحظات تحضير أو تفضيلات الزبون..."
                                            className="mt-4 w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/40"
                                            rows={2}
                                        />
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="mt-6 grid gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <span>الخصومات</span>
                                <div className="flex flex-wrap gap-2">
                                    {QUICK_DISCOUNTS.map((quick) => (
                                        <button
                                            key={quick.label}
                                            type="button"
                                            onClick={() => handleApplyQuickDiscount(quick.value, quick.type)}
                                            className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/70 transition hover:bg-white/20"
                                        >
                                            {quick.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="grid gap-4 sm:grid-cols-3">
                                <div className="space-y-2">
                                    <span className="block text-xs text-white/60">نوع الخصم</span>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setDiscountType('percent')}
                                            className={`flex-1 rounded-2xl px-3 py-2 text-xs font-medium transition ${
                                                discountType === 'percent'
                                                    ? 'bg-primary text-primary-content'
                                                    : 'bg-white/10 text-white/70'
                                            }`}
                                        >
                                            نسبة مئوية
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setDiscountType('amount')}
                                            className={`flex-1 rounded-2xl px-3 py-2 text-xs font-medium transition ${
                                                discountType === 'amount'
                                                    ? 'bg-primary text-primary-content'
                                                    : 'bg-white/10 text-white/70'
                                            }`}
                                        >
                                            قيمة ثابتة
                                        </button>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <span className="block text-xs text-white/60">قيمة الخصم</span>
                                    <input
                                        type="number"
                                        min={0}
                                        value={discount}
                                        onChange={(event) => setDiscount(Math.max(0, Number(event.target.value) || 0))}
                                        className="w-full rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <span className="block text-xs text-white/60">رسوم الخدمة</span>
                                    <input
                                        type="number"
                                        min={0}
                                        value={serviceFee}
                                        onChange={(event) => setServiceFee(Math.max(0, Number(event.target.value) || 0))}
                                        className="w-full rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
                                    />
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="flex items-center gap-2 text-xs text-white/70">
                                    <input
                                        type="checkbox"
                                        checked={redeemLoyalty}
                                        onChange={(event) => setRedeemLoyalty(event.target.checked)}
                                        className="h-4 w-4 rounded border-white/20 bg-white/10"
                                    />
                                    استخدام برنامج الولاء ({loyaltyPoints} نقطة متاحة)
                                </label>
                                {redeemLoyalty && (
                                    <span className="text-xs text-emerald-200">
                                        سيتم خصم {formatCurrency(loyaltyRedeemValue)} من الإجمالي
                                    </span>
                                )}
                            </div>
                        </div>

                        <div className="mt-6 space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">
                            <div className="flex justify-between">
                                <span>المجموع الفرعي</span>
                                <span>{formatCurrency(subtotal)}</span>
                            </div>
                            <div className="flex justify-between text-white/70">
                                <span>الخصم المطبق</span>
                                <span>-{formatCurrency(appliedDiscount)}</span>
                            </div>
                            <div className="flex justify-between text-white/70">
                                <span>الضريبة ({Math.round(TAX_RATE * 100)}%)</span>
                                <span>{formatCurrency(taxAmount)}</span>
                            </div>
                            <div className="flex justify-between text-white/70">
                                <span>رسوم الخدمة</span>
                                <span>{formatCurrency(serviceFee)}</span>
                            </div>
                            {loyaltyRedeemValue > 0 && (
                                <div className="flex justify-between text-emerald-200">
                                    <span>خصم الولاء</span>
                                    <span>-{formatCurrency(loyaltyRedeemValue)}</span>
                                </div>
                            )}
                            <div className="flex justify-between border-t border-white/10 pt-3 text-base font-semibold text-white">
                                <span>الإجمالي المستحق</span>
                                <span>{formatCurrency(totalDue)}</span>
                            </div>
                            <div className="flex justify-between text-xs text-white/60">
                                <span>عدد العناصر</span>
                                <span>{totalItems}</span>
                            </div>
                        </div>

                        <div className="mt-6 grid gap-4 text-sm text-white/80 sm:grid-cols-2">
                            <div className="space-y-2">
                                <span className="block text-xs text-white/60">اسم الزبون</span>
                                <input
                                    type="text"
                                    value={customerName}
                                    onChange={(event) => setCustomerName(event.target.value)}
                                    className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white focus:border-primary focus:outline-none"
                                />
                            </div>
                            <div className="space-y-2">
                                <span className="block text-xs text-white/60">ملاحظات الطلب</span>
                                <input
                                    type="text"
                                    value={orderNotes}
                                    onChange={(event) => setOrderNotes(event.target.value)}
                                    className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white focus:border-primary focus:outline-none"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <h2 className="text-xl font-semibold">خيارات الدفع</h2>
                        <p className="mt-1 text-sm text-white/60">اختر وسيلة الدفع المناسبة وقم بإتمام المعاملة بثقة.</p>
                        <div className="mt-4 grid gap-3">
                            {PAYMENT_METHODS.map((method) => (
                                <button
                                    key={method.id}
                                    type="button"
                                    onClick={() => setPaymentMethod(method.id)}
                                    className={`rounded-2xl border px-4 py-3 text-left transition ${
                                        paymentMethod === method.id
                                            ? 'border-primary bg-primary/20 text-white'
                                            : 'border-white/10 bg-white/5 text-white/70 hover:border-primary/50'
                                    }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-semibold">{method.label}</span>
                                        {paymentMethod === method.id && <span className="text-xs text-primary/80">محدد</span>}
                                    </div>
                                    <p className="mt-1 text-xs text-white/60">{method.description}</p>
                                </button>
                            ))}
                        </div>
                        {paymentMethod === 'split' && (
                            <div className="mt-4 space-y-2 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-white/70">
                                <p className="font-semibold text-white">توزيع الدفع المقسّم</p>
                                <p>قسّم المبلغ بين وسيلتين (مثال: 60% بطاقة، 40% نقداً) مع تأكيد الرصيد قبل إغلاق الطلب.</p>
                            </div>
                        )}
                        <div className="mt-6 grid gap-3 sm:grid-cols-3">
                            <button
                                type="button"
                                onClick={handleHoldOrder}
                                className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold text-white transition hover:border-primary/70 hover:bg-primary/10"
                            >
                                تعليق الطلب
                            </button>
                            <button
                                type="button"
                                onClick={handleReset}
                                className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold text-white transition hover:border-primary/70 hover:bg-primary/10"
                            >
                                تفريغ السلة
                            </button>
                            <button
                                type="button"
                                onClick={handleCompleteOrder}
                                disabled={cart.length === 0}
                                className="rounded-2xl bg-primary px-4 py-3 text-sm font-semibold text-primary-content transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/40"
                            >
                                إتمام الطلب
                            </button>
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">الطلبات المعلقة</h2>
                            <span className="text-xs text-white/60">{heldOrders.length} طلب</span>
                        </div>
                        <div className="mt-4 space-y-3 text-sm text-white/70">
                            {heldOrders.length === 0 && <p>لا توجد طلبات معلقة حالياً.</p>}
                            {heldOrders.map((order) => (
                                <div
                                    key={order.id}
                                    className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 sm:flex-row sm:items-center sm:justify-between"
                                >
                                    <div>
                                        <p className="font-semibold text-white">{order.label}</p>
                                        <p className="text-xs text-white/50">
                                            {formatDateTime(new Date(order.createdAt))} • {order.customerName}
                                        </p>
                                        <p className="text-xs text-white/60">
                                            إجمالي تقديري: {formatCurrency(order.estimatedTotal)} • عناصر: {order.cart.reduce((sum, line) => sum + line.quantity, 0)}
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleResumeOrder(order.id)}
                                        className="rounded-full bg-primary px-4 py-2 text-xs font-semibold text-primary-content transition hover:bg-primary/90"
                                    >
                                        استرجاع الطلب
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl shadow-black/20">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">معاينة الفاتورة</h2>
                            <span className="text-xs text-white/60">تُحدَّث مباشرة بعد إتمام الطلب</span>
                        </div>
                        {recentReceipt ? (
                            <pre className="mt-4 max-h-64 overflow-auto rounded-2xl border border-white/10 bg-black/40 text-xs text-emerald-100">
                                {recentReceipt}
                            </pre>
                        ) : (
                            <p className="mt-4 text-sm text-white/60">
                                بعد إتمام الطلب ستظهر نسخة مطبوعة من الفاتورة هنا لمراجعتها أو إرسالها بالبريد الإلكتروني.
                            </p>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default PosSystem;
