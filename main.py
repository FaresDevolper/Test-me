import os
import io
import re
import time
import random
import asyncio
import threading

import discord
from flask import Flask
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_AR = True
except Exception:
    HAS_AR = False

# ------------------------------------------------------------------
# الإعدادات (غيّرها براحتك)
# ------------------------------------------------------------------
COMMAND = "اختبرني"          # أمر بدء اللعبة (بدون سلاش وبدون بريفكس)
CORNER_TEXT = "Test me"       # الكلمة داخل المربع الصغير فوق يمين
ROUND_TIMEOUT = 15            # مهلة الجولة بالثواني
IMG_W, IMG_H = 1000, 520      # مقاس الصورة
BG_FILE = "background.png"    # ضع هنا الخلفية حقتك (اختياري)
BTN_COLOR = (137, 133, 184)   # #8985b8 لون المستطيل
CORNER_COLOR = (137, 133, 184) # #8985b8 لون المربع الصغير
TEXT_COLOR = (255, 255, 255)
WIN_MESSAGE = "الإجابة صحيحة 🫡"   # يرسل مع منشن الفائز
STOP_COMMAND = "وقف الاختبار"      # أمر الأونر فقط
BUSY_MESSAGE = "مختبرك يا وحش، جاوب لا تصرف"
NO_WINNER_MESSAGE = "ما في أحد جاوب إجابة صحيحة"
OWNER_ID = int(os.environ.get("OWNER_ID", "912349519990095892"))  # اختياري: ايدي حسابك، وإلا يؤخذ تلقائياً من مالك البوت

# ------------------------------------------------------------------
# الكلمات: english:معنى1/معنى2/معنى3
# أضف أي كلمات جديدة بنفس الصيغة
# ------------------------------------------------------------------
RAW_WORDS = """
fire:نار/حريق
water:ماء/مياه
sun:شمس
moon:قمر
star:نجم/نجمة
sky:سماء
earth:ارض/أرض
wind:ريح/هواء
rain:مطر
snow:ثلج
cloud:سحابة/غيمة
sea:بحر
river:نهر
mountain:جبل
desert:صحراء
forest:غابة
tree:شجرة
flower:زهرة/وردة
grass:عشب
stone:حجر
sand:رمل
house:بيت/منزل
door:باب
window:نافذة/شباك
room:غرفة
kitchen:مطبخ
bed:سرير
chair:كرسي
table:طاولة
book:كتاب
pen:قلم
paper:ورقة/ورق
school:مدرسة
teacher:معلم/مدرس
student:طالب
friend:صديق
family:عائلة/اسرة
mother:أم/ام/والدة
father:أب/اب/والد
brother:أخ/اخ/اخو
sister:أخت/اخت
son:ابن
daughter:بنت/ابنة
king:ملك
queen:ملكة
prince:أمير/امير
people:ناس/شعب
man:رجل
woman:امرأة/مرأة/انثى
boy:ولد
girl:بنت/فتاة
child:طفل
baby:رضيع/طفل
dog:كلب
cat:قطة/قط
horse:حصان
cow:بقرة
sheep:خروف/غنم
camel:جمل
lion:اسد/أسد
tiger:نمر
wolf:ذئب
fox:ثعلب
bear:دب
monkey:قرد
elephant:فيل
snake:ثعبان/افعى
bird:طائر/عصفور
fish:سمكة/سمك
eagle:نسر/عقاب
bee:نحلة
ant:نملة
spider:عنكبوت
apple:تفاحة/تفاح
banana:موز/موزة
orange:برتقال/برتقالة
grape:عنب
lemon:ليمون
watermelon:بطيخ/بطيخة
strawberry:فراولة
tomato:طماطم/بندورة
potato:بطاطس/بطاطا
onion:بصل
garlic:ثوم
rice:رز/ارز/أرز
bread:خبز
milk:حليب/لبن
egg:بيضة/بيض
meat:لحم
chicken:دجاج/دجاجة
cheese:جبن/جبنة
sugar:سكر
salt:ملح
coffee:قهوة
tea:شاي
juice:عصير
honey:عسل
cake:كيك/كعكة
car:سيارة
bus:حافلة/باص
train:قطار
plane:طائرة
ship:سفينة
bike:دراجة
road:طريق/شارع
bridge:جسر
city:مدينة
village:قرية
country:بلد/دولة
market:سوق
hospital:مستشفى
doctor:طبيب/دكتور
police:شرطة
soldier:جندي
money:مال/فلوس/نقود
gold:ذهب
silver:فضة
diamond:الماس/ألماس
key:مفتاح
lock:قفل
phone:هاتف/جوال/تلفون
computer:حاسوب/كمبيوتر
screen:شاشة
camera:كاميرا
music:موسيقى
song:اغنية/أغنية
game:لعبة
ball:كرة
gift:هدية
dream:حلم
love:حب
hate:كره
hope:امل/أمل
fear:خوف
anger:غضب
joy:فرح/سعادة
sadness:حزن
peace:سلام
war:حرب
life:حياة
death:موت
time:وقت/زمن
day:يوم
night:ليل/ليلة
morning:صباح
evening:مساء
week:اسبوع/أسبوع
month:شهر
year:سنة/عام
today:اليوم
tomorrow:غدا/بكرة
yesterday:امس/أمس/البارحة
big:كبير
small:صغير
long:طويل
short:قصير
fast:سريع
slow:بطيء/بطي
hot:حار/حار جدا/ساخن
cold:بارد
new:جديد
old:قديم/عجوز
good:جيد/حسن/زين
bad:سيء/سيئ
beautiful:جميل
ugly:قبيح
strong:قوي
weak:ضعيف
rich:غني
poor:فقير
happy:سعيد/مسرور
sad:حزين
clean:نظيف
dirty:وسخ/متسخ
easy:سهل
hard:صعب
heavy:ثقيل
light:خفيف/ضوء
dark:مظلم/ظلام
empty:فارغ
full:ممتلئ/مليان
open:مفتوح/افتح
close:اغلق/أغلق/قريب
run:يجري/اركض/ركض
walk:يمشي/امشي/مشي
jump:يقفز/قفز
sleep:ينام/نوم
eat:ياكل/يأكل/اكل/أكل
drink:يشرب/شرب
read:يقرأ/يقرا/قراءة
write:يكتب/كتابة
speak:يتكلم/يتحدث/تكلم
listen:يستمع/استمع
see:يرى/يشوف/شاهد
think:يفكر/فكر
know:يعرف/عرف
help:مساعدة/ساعد/يساعد
give:يعطي/اعط/أعط
take:ياخذ/يأخذ/خذ
buy:يشتري/اشتري
sell:يبيع/بيع
win:يفوز/فوز
lose:يخسر/خسارة
red:احمر/أحمر
blue:ازرق/أزرق
green:اخضر/أخضر
yellow:اصفر/أصفر
black:اسود/أسود
white:ابيض/أبيض
purple:بنفسجي/ارجواني
pink:وردي
brown:بني
gray:رمادي
head:راس/رأس
hand:يد
eye:عين
ear:اذن/أذن
nose:انف/أنف
mouth:فم
heart:قلب
leg:رجل/ساق
hair:شعر
face:وجه
shirt:قميص
shoes:حذاء/جزمة
hat:قبعة/طاقية
bag:حقيبة/شنطة
umbrella:مظلة/شمسية
mirror:مرآة/مراية
clock:ساعة
knife:سكين
spoon:ملعقة
cup:كوب/فنجان
plate:صحن/طبق
bottle:زجاجة/قارورة
box:صندوق/علبة
rope:حبل
wall:جدار/حائط
floor:ارض/أرض/ارضية
roof:سقف
garden:حديقة
beach:شاطئ
island:جزيرة
storm:عاصفة
thunder:رعد
lightning:برق
ice:جليد/ثلج
smoke:دخان
shadow:ظل
voice:صوت
silence:صمت/سكوت
secret:سر
truth:حقيقة/صدق
lie:كذبة/كذب
power:قوة
brave:شجاع
smart:ذكي
lazy:كسول
angry:غاضب
tired:متعب/تعبان
hungry:جائع/جوعان
thirsty:عطشان
""".strip()


def _norm(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)  # تشكيل + تطويل
    text = (text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
                .replace("ى", "ي").replace("ة", "ه")
                .replace("ؤ", "و").replace("ئ", "ي"))
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.startswith("ال") and len(text) > 4:
        text = text[2:]
    return text


WORDS = {}
for line in RAW_WORDS.splitlines():
    line = line.strip()
    if ":" not in line:
        continue
    eng, ar = line.split(":", 1)
    WORDS[eng.strip()] = {_norm(a) for a in ar.split("/") if a.strip()}
WORD_LIST = list(WORDS.keys())

# ------------------------------------------------------------------
# الصورة
# ------------------------------------------------------------------
FONT_EN_CANDIDATES = [
    "fonts/font.ttf",
    "fonts/font.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size: int):
    for p in FONT_EN_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _ar(text: str) -> str:
    try:
        from PIL import features
        if features.check("raqm"):
            return text  # Pillow يعالج العربي بنفسه
    except Exception:
        pass
    if HAS_AR:
        return get_display(arabic_reshaper.reshape(text))
    return text


def _background() -> Image.Image:
    if os.path.exists(BG_FILE):
        bg = Image.open(BG_FILE).convert("RGB")
        # قص وتكبير ليناسب المقاس
        ratio = max(IMG_W / bg.width, IMG_H / bg.height)
        bg = bg.resize((int(bg.width * ratio), int(bg.height * ratio)), Image.LANCZOS)
        left = (bg.width - IMG_W) // 2
        top = (bg.height - IMG_H) // 2
        return bg.crop((left, top, left + IMG_W, top + IMG_H))
    # خلفية افتراضية داكنة بتدرج
    img = Image.new("RGB", (IMG_W, IMG_H), (4, 4, 14))
    px = ImageDraw.Draw(img)
    for y in range(IMG_H):
        t = y / IMG_H
        px.line([(0, y), (IMG_W, y)], fill=(int(6 + 14 * t), int(6 + 8 * t), int(20 + 40 * t)))
    return img


def make_image(word: str) -> io.BytesIO:
    img = _background().convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # المربع الأزرق في النص
    bw, bh = 640, 150
    bx0 = (IMG_W - bw) // 2
    by0 = (IMG_H - bh) // 2 + 30
    bx1, by1 = bx0 + bw, by0 + bh

    # ظل خفيف
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((bx0, by0 + 8, bx1, by1 + 8), 18, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, shadow)

    d.rounded_rectangle((bx0, by0, bx1, by1), 18, fill=BTN_COLOR + (255,))

    # المربع الصغير يمين فوق (يتداخل مع الزاوية)
    cf = _font(34)
    label = _ar(CORNER_TEXT)
    lb = d.textbbox((0, 0), label, font=cf)
    lw, lh = lb[2] - lb[0], lb[3] - lb[1]
    pad_x, pad_y = 30, 18
    cw, ch = lw + pad_x * 2, lh + pad_y * 2
    cx1 = bx1 + 40
    cy1 = by0 + ch // 2
    cx0, cy0 = cx1 - cw, cy1 - ch
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, fill=CORNER_COLOR + (255,), outline=(8, 8, 24, 255), width=4)
    d.text((cx0 + pad_x - lb[0], cy0 + pad_y - lb[1]), label, font=cf, fill=TEXT_COLOR)

    # الكلمة الإنجليزية، نصغر الخط لو طويلة
    size = 84
    wf = _font(size)
    wb = d.textbbox((0, 0), word, font=wf)
    while (wb[2] - wb[0]) > bw - 60 and size > 30:
        size -= 4
        wf = _font(size)
        wb = d.textbbox((0, 0), word, font=wf)
    tw, th = wb[2] - wb[0], wb[3] - wb[1]
    d.text((bx0 + (bw - tw) / 2 - wb[0], by0 + (bh - th) / 2 - wb[1]), word, font=wf, fill=TEXT_COLOR)

    final = Image.alpha_composite(img, layer).convert("RGB")
    buf = io.BytesIO()
    final.save(buf, "PNG")
    buf.seek(0)
    return buf


# ------------------------------------------------------------------
# البوت
# ------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# channel_id -> {"word": str, "answers": set, "id": int}
active = {}
last_word = {}
owner_ids = set()
_round_counter = 0


def pick_word(channel_id: int) -> str:
    w = random.choice(WORD_LIST)
    while w == last_word.get(channel_id) and len(WORD_LIST) > 1:
        w = random.choice(WORD_LIST)
    last_word[channel_id] = w
    return w


async def round_timer(channel, round_id: int):
    await asyncio.sleep(ROUND_TIMEOUT)
    rnd = active.get(channel.id)
    if rnd and rnd["id"] == round_id:  # لسه نفس الجولة وما أحد فاز
        active.pop(channel.id, None)
        try:
            await channel.send(NO_WINNER_MESSAGE)
        except Exception as e:
            print("timeout send error:", e)


@client.event
async def on_ready():
    global owner_ids
    if OWNER_ID:
        owner_ids = {OWNER_ID}
    else:
        try:
            info = await client.application_info()
            if info.team:
                owner_ids = {m.id for m in info.team.members} | {info.team.owner_id}
            else:
                owner_ids = {info.owner.id}
        except Exception as e:
            print("owner detect error:", e)
    print(f"Logged in as {client.user} | words: {len(WORD_LIST)} | owners: {owner_ids}")


@client.event
async def on_message(message: discord.Message):
    global _round_counter
    if message.author.bot or message.guild is None:
        return

    content = message.content.strip()
    cid = message.channel.id

    # أمر الأونر: وقف الاختبار
    if content == STOP_COMMAND:
        if message.author.id in owner_ids:
            if active.pop(cid, None) is not None:
                await message.channel.send("تم إيقاف الاختبار")
        return

    # بدء جولة جديدة
    if content == COMMAND:
        if cid in active:
            await message.reply(BUSY_MESSAGE, mention_author=True)
            return
        word = pick_word(cid)
        _round_counter += 1
        rid = _round_counter
        active[cid] = {"word": word, "answers": WORDS[word], "id": rid}
        try:
            await message.channel.send(file=discord.File(make_image(word), filename="test.png"))
        except Exception as e:
            active.pop(cid, None)
            print("send error:", e)
            return
        asyncio.create_task(round_timer(message.channel, rid))
        return

    # فحص الإجابة
    rnd = active.get(cid)
    if rnd and _norm(content) in rnd["answers"]:
        active.pop(cid, None)  # أول واحد فقط يفوز
        await message.channel.send(f"{message.author.mention} {WIN_MESSAGE}")


# ------------------------------------------------------------------
# سيرفر صغير عشان Render + UptimeRobot
# ------------------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive"


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    token = os.environ.get("TOKEN")
    if not token:
        raise SystemExit("حط التوكن في متغير البيئة TOKEN")
    threading.Thread(target=run_web, daemon=True).start()
    client.run(token)
