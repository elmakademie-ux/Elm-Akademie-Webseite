// Default character bible. Appearance text is the single source of truth that
// gets injected into every video / image prompt to keep looks consistent.
// Everything here is editable in the Character Studio and saved to data/.
export const STYLE_BIBLE =
  'Stylised 3D animated family sitcom, soft cinematic lighting, warm saturated colours, ' +
  'expressive cartoon faces, smooth character animation, shallow depth of field, vertical 9:16 framing';

export const DEFAULT_CHARACTERS = [
  {
    id: 'bob', name: 'Bob', age: 42, role: 'Father', color: '#e8a33d',
    tagline: 'Funny, lazy father',
    personality: 'Lovable couch potato. Avoids chores with elaborate excuses, big heart, terrible ideas.',
    appearance: 'stocky middle-aged man, round friendly face, messy short brown hair, light stubble, rumpled green t-shirt, grey sweatpants, fluffy slippers',
    expressions: ['neutral', 'happy', 'sleepy', 'panicked', 'smug', 'guilty', 'surprised', 'laughing'],
    voice: { description: 'Warm, low, slow baritone with a lazy drawl', provider: 'elevenlabs', voiceId: '', stability: 0.5, similarity: 0.75 },
  },
  {
    id: 'lucy', name: 'Lucy', age: 39, role: 'Mother', color: '#d9534f',
    tagline: 'Intelligent, sarcastic mother',
    personality: 'Sharp-witted and always three steps ahead. Dry sarcasm, secretly adores the chaos.',
    appearance: 'slim woman, auburn hair in a loose bun, rectangular glasses, teal cardigan over a white blouse, dark jeans, expressive raised eyebrow',
    expressions: ['neutral', 'happy', 'unimpressed', 'sarcastic', 'angry', 'amused', 'surprised', 'exhausted'],
    voice: { description: 'Clear, medium-pitched, dry and precise delivery', provider: 'elevenlabs', voiceId: '', stability: 0.55, similarity: 0.75 },
  },
  {
    id: 'max', name: 'Max', age: 8, role: 'Son', color: '#3fa7d6',
    tagline: 'Mischievous 8-year-old',
    personality: 'Prankster and schemer. Fast talker, always has a plan that goes slightly wrong.',
    appearance: 'energetic 8-year-old boy, spiky dark-blond hair, freckles, gap-toothed grin, red hoodie, blue shorts, sneakers',
    expressions: ['neutral', 'happy', 'scheming', 'caught', 'surprised', 'laughing', 'innocent', 'angry'],
    voice: { description: 'Bright, fast, mischievous young boy', provider: 'elevenlabs', voiceId: '', stability: 0.4, similarity: 0.75 },
  },
  {
    id: 'emma', name: 'Emma', age: 6, role: 'Daughter', color: '#b57edc',
    tagline: 'Clever 6-year-old',
    personality: 'Small but wise. Deadpan observations that expose everyone else\'s nonsense.',
    appearance: 'small 6-year-old girl, dark hair in two pigtails with yellow ribbons, large round eyes, purple dress, white tights, carries a tiny notebook',
    expressions: ['neutral', 'happy', 'deadpan', 'curious', 'proud', 'surprised', 'giggling', 'suspicious'],
    voice: { description: 'Small, sweet, calm and slightly too-wise child voice', provider: 'elevenlabs', voiceId: '', stability: 0.5, similarity: 0.75 },
  },
  {
    id: 'rose', name: 'Grandma Rose', age: 74, role: 'Grandmother', color: '#7bc67b', aliases: ['rose', 'grandma'],
    tagline: 'Unpredictable grandmother',
    personality: 'Sweet one second, wildly chaotic the next. Says shocking things with total innocence.',
    appearance: 'elderly woman, silver hair in a tidy bun, round gold glasses, lilac cardigan, pearl necklace, floral skirt, wooden cane covered in stickers',
    expressions: ['neutral', 'happy', 'sweet', 'mischievous', 'confused', 'shocked', 'cackling', 'sleepy'],
    voice: { description: 'Warm, slightly raspy elderly woman, sudden energy spikes', provider: 'elevenlabs', voiceId: '', stability: 0.35, similarity: 0.75 },
  },
].map((c) => ({ referenceImages: [], ...c }));
