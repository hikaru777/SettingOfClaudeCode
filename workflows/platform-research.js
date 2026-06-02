export const meta = {
  name: 'platform-research',
  description: '全SNSプラットフォーム横断リサーチ。各スライスがリトライ+フォールバックで自己修復し、空返答を1体も出さない',
  whenToUse: 'SNSの全プラットフォームで「何が受けているか」等を大規模並列リサーチしたい時。args={topic, platforms?, lensesPerPlatform?, retries?, includeJP?}',
  phases: [
    { title: 'Research', detail: '各(プラットフォーム×レンズ)を並列調査。失敗はリトライ→フォールバック→保証スタブで必ず非空' },
    { title: 'Heal', detail: '不足スライスを再調査して埋める' },
    { title: 'Synthesize', detail: '全成果をバズ型ライブラリと攻略レポートに統合' },
  ],
}

// ───────────────────────── パラメータ ─────────────────────────
const A = (args && typeof args === 'object') ? args : {}
const TOPIC = A.topic || 'SNSで今エンタメとして何が受けているか（2026年）'
const RETRIES = Number.isInteger(A.retries) ? A.retries : 2
const LENSES_PER_PLATFORM = Number.isInteger(A.lensesPerPlatform) ? A.lensesPerPlatform : 5
const INCLUDE_JP = A.includeJP !== false

// 全プラットフォーム（グローバル + 日本）
const GLOBAL_PLATFORMS = [
  'X (Twitter)', 'Instagram', 'TikTok', 'YouTube', 'YouTube Shorts',
  'Facebook', 'Threads', 'LinkedIn', 'Reddit', 'Pinterest',
  'Snapchat', 'Twitch', 'Bluesky', 'Tumblr', 'Discord',
]
const JP_PLATFORMS = ['note (日本)', 'LINE VOOM', 'niconico (ニコニコ)', 'mixi2', '5ch/まとめ系']
const ALL_PLATFORMS = INCLUDE_JP ? [...GLOBAL_PLATFORMS, ...JP_PLATFORMS] : GLOBAL_PLATFORMS
const PLATFORMS = Array.isArray(A.platforms) && A.platforms.length > 0 ? A.platforms : ALL_PLATFORMS

// 各プラットフォームに当てる調査レンズ（角度）。LENSES_PER_PLATFORM で本数を絞れる
const ALL_LENSES = [
  { key: 'hooks', q: 'バズっている投稿/動画の「型・フック・掴み」を具体例つきで' },
  { key: 'genres', q: '今伸びているジャンル/テーマと、その勢い（上昇/安定/飽和）' },
  { key: 'algo', q: 'アルゴリズムが優遇する要素・最重要シグナル（完了率/シェア/会話等）' },
  { key: 'dead', q: '失速・飽和して今から入ると不利な型/ジャンル' },
  { key: 'local', q: '該当プラットフォーム特有の文化・流行・ユーザー心理の動き' },
]
const LENSES = ALL_LENSES.slice(0, Math.max(1, Math.min(ALL_LENSES.length, LENSES_PER_PLATFORM)))

// 調査対象スライス（= 派遣社員1人ぶん）
const SLICES = []
for (const platform of PLATFORMS) {
  for (const lens of LENSES) SLICES.push({ platform, lens })
}

// ───────────────────────── スキーマ ─────────────────────────
const SLICE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    status: { type: 'string', enum: ['ok', 'thin', 'insufficient'], description: 'ok=十分 / thin=薄い / insufficient=情報なし' },
    winningFormats: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          name: { type: 'string' },
          description: { type: 'string' },
          whyItWorks: { type: 'string', description: '心理/アルゴリズム的理由' },
          exampleOrEvidence: { type: 'string' },
        },
        required: ['name', 'description', 'whyItWorks', 'exampleOrEvidence'],
      },
    },
    hookPatterns: { type: 'array', items: { type: 'string' } },
    risingGenres: { type: 'array', items: { type: 'string' } },
    saturatedGenres: { type: 'array', items: { type: 'string' } },
    algorithmSignals: { type: 'array', items: { type: 'string' } },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['status', 'winningFormats', 'hookPatterns', 'risingGenres', 'saturatedGenres', 'algorithmSignals', 'sources'],
}

// 使える結果か判定（空返答ガードの心臓部）
function isUsable(r) {
  if (!r || typeof r !== 'object') return false
  const wf = Array.isArray(r.winningFormats) ? r.winningFormats.length : 0
  const hp = Array.isArray(r.hookPatterns) ? r.hookPatterns.length : 0
  return wf >= 2 || (wf >= 1 && hp >= 2)
}
function hasAnything(r) {
  if (!r || typeof r !== 'object') return false
  return (
    (r.winningFormats?.length || 0) +
    (r.hookPatterns?.length || 0) +
    (r.risingGenres?.length || 0) +
    (r.algorithmSignals?.length || 0)
  ) > 0
}
function emptyStub(slice, note) {
  return {
    platform: slice.platform, lens: slice.lens.key,
    status: 'insufficient', winningFormats: [], hookPatterns: [],
    risingGenres: [], saturatedGenres: [], algorithmSignals: [],
    sources: [], source: 'stub', note,
  }
}

function primaryPrompt(slice, attempt) {
  const nudge = attempt === 0
    ? ''
    : `\n\n【再調査 ${attempt}回目】前回は情報が薄かった。検索クエリを変え（英語/日本語、年号、"viral"/"trend"/"バズ"/"伸びる"等を組合せ）、別ソースを当たれ。それでも乏しければ status:"thin" で分かった分だけ確実に返せ。`
  return `君はSNS横断リサーチの派遣リサーチャーだ。WebSearchツールを必ず複数回使え（"select:WebSearch" でツールを読み込んでから検索）。

調査対象: 【${slice.platform}】について、テーマ「${TOPIC}」の観点で、${slice.lens.q}。

要件:
- 推測で埋めず、実際にWeb検索して2026年の最新を掴め
- winningFormats は最低2件、hookPatterns は具体的な言い回しレベルで
- なぜ受けるか(心理/アルゴリズム)まで言語化しろ
- 参照URLを sources に残せ
- 十分に取れたら status:"ok"。${nudge}

構造化出力で返せ。`
}

function fallbackPrompt(slice) {
  return `君はSNSマーケティングの専門家だ。Web検索が振るわなかったので、君の知識ベースで確実に答えろ（検索してもよいが必須ではない）。

対象: 【${slice.platform}】 / テーマ「${TOPIC}」 / 観点: ${slice.lens.q}

このプラットフォームで一般に通用している「受ける型・フック・アルゴ特性」を、最低でも winningFormats 1件 + hookPatterns 2件は必ず出せ。確証が薄いものは status:"thin"。完全に知らない場合のみ status:"insufficient"。空配列だけで返すことは禁止。

構造化出力で返せ。`
}

// 1スライスを自己修復つきで調査する。絶対に null/空ホールを返さない。
async function researchSlice(slice, phaseLabel) {
  const label = `${slice.platform}:${slice.lens.key}`
  // 1) 主調査をリトライ
  for (let attempt = 0; attempt <= RETRIES; attempt++) {
    let r = null
    try {
      r = await agent(primaryPrompt(slice, attempt), {
        label: attempt === 0 ? `research:${label}` : `retry${attempt}:${label}`,
        phase: phaseLabel, schema: SLICE_SCHEMA,
      })
    } catch (_e) { r = null }
    if (isUsable(r)) return { ...r, platform: slice.platform, lens: slice.lens.key, source: 'web' }
  }
  // 2) フォールバック（知識ベース）
  let fb = null
  try {
    fb = await agent(fallbackPrompt(slice), {
      label: `fallback:${label}`, phase: phaseLabel, schema: SLICE_SCHEMA,
    })
  } catch (_e) { fb = null }
  if (hasAnything(fb)) {
    return {
      ...fb, platform: slice.platform, lens: slice.lens.key,
      status: isUsable(fb) ? 'thin' : (fb.status || 'thin'), source: 'fallback',
    }
  }
  // 3) 保証スタブ（それでもダメなら明示的に「情報なし」を返す＝沈黙させない）
  return emptyStub(slice, 'リトライ+フォールバックでも十分な情報が得られなかった')
}

// ───────────────────────── 実行 ─────────────────────────
phase('Research')
log(`対象: ${PLATFORMS.length}プラットフォーム × ${LENSES.length}レンズ = ${SLICES.length}スライス（リトライ${RETRIES}回+フォールバック付き）`)

let results = await parallel(SLICES.map((slice) => () => researchSlice(slice, 'Research')))
// parallel自体がthrowをnull化するが、researchSliceは必ずオブジェクトを返すので念のため埋める
results = results.map((r, i) => r || emptyStub(SLICES[i], 'スライス実行が中断された'))

const insufficient = results.filter((r) => r.status === 'insufficient')
const thin = results.filter((r) => r.status === 'thin')
log(`一次完了: ok ${results.length - insufficient.length - thin.length} / thin ${thin.length} / insufficient ${insufficient.length}`)

// ── Heal: 不足スライスをもう一度だけ埋めにいく ──
if (insufficient.length > 0) {
  phase('Heal')
  log(`不足 ${insufficient.length} スライスを再調査`)
  const healed = await parallel(
    insufficient.map((r) => () => {
      const slice = SLICES.find((s) => s.platform === r.platform && s.lens.key === r.lens) || { platform: r.platform, lens: { key: r.lens, q: '受ける型・フック・アルゴ特性' } }
      return researchSlice(slice, 'Heal')
    })
  )
  // 置き換え
  for (let i = 0; i < healed.length; i++) {
    const h = healed[i] || insufficient[i]
    const idx = results.findIndex((r) => r.platform === h.platform && r.lens === h.lens)
    if (idx >= 0) results[idx] = h
  }
}

const stillEmpty = results.filter((r) => r.status === 'insufficient')
log(`最終: 全${results.length}スライス取得済み（空返答0を保証）。残insufficient=${stillEmpty.length}（情報自体が存在しない領域のみ）`)

// ── Synthesize ──
phase('Synthesize')
const SYN_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    topPatterns: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          pattern: { type: 'string' }, whyItWorks: { type: 'string' },
          applicableTo: { type: 'string' }, exampleHooks: { type: 'array', items: { type: 'string' } },
        },
        required: ['pattern', 'whyItWorks', 'applicableTo', 'exampleHooks'],
      },
    },
    platformPlaybook: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { platform: { type: 'string' }, whatWins: { type: 'string' } },
        required: ['platform', 'whatWins'],
      },
    },
    risingGenres: { type: 'array', items: { type: 'string' } },
    saturatedGenres: { type: 'array', items: { type: 'string' } },
    actionableTemplates: { type: 'array', items: { type: 'string' } },
    coverageNote: { type: 'string', description: '情報が薄かった/取れなかったプラットフォームの明示（沈黙禁止）' },
    report: { type: 'string', description: '日本語マークダウン統合レポート' },
  },
  required: ['topPatterns', 'platformPlaybook', 'risingGenres', 'saturatedGenres', 'actionableTemplates', 'coverageNote', 'report'],
}

const coverage = {
  total: results.length,
  thin: thin.map((r) => `${r.platform}:${r.lens}`),
  insufficient: stillEmpty.map((r) => `${r.platform}:${r.lens}`),
}

const synthesis = await agent(
  `君はSNSカンパニーのストラテジストだ。全プラットフォーム横断の調査結果(${results.length}スライス)を統合し、実戦で使えるバズ型ライブラリと攻略レポートにせよ。

テーマ: ${TOPIC}

調査結果(JSON):
${JSON.stringify(results)}

カバレッジ情報(JSON):
${JSON.stringify(coverage)}

要件:
- 複数プラットフォームで繰り返し現れた型を topPatterns に強い順で
- 各プラットフォームの勝ち筋を platformPlaybook に1行で
- 飽和/狙い目を区別
- 明日から使える穴埋めテンプレを actionableTemplates に
- coverageNote に「情報が薄かった/取れなかったプラットフォーム」を正直に明記（沈黙して網羅したフリをするな）
- report は日本語マークダウンで自社アカウントを伸ばす視点で

構造化出力で返せ。`,
  { label: 'synthesize:strategist', phase: 'Synthesize', schema: SYN_SCHEMA }
)

return { synthesis, coverage, sliceCount: results.length }
