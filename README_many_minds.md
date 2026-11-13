# Many Minds 万意 / Many Circles 招待 🌿

> 票を持たない声を、採決の前に、問う。
> *Before a vote, ask the voices that have no vote.*

A small simulation of one idea: **before humans and AIs vote, the voices that cannot vote are asked first**: the animals, the land, the sea, the sick and the weak, the children not yet born, and a seat for what we have not yet met.
一つの考えの小さなシミュレーションです。**人間とAIが投票する前に、票を持たない声に、先に問う。** 動物たち、大地、海、病める者・弱き者、まだ生まれていない子ら、そして、まだ出会っていない存在のための席。

This repository holds two motions of the Resonant Civilization / 共鳴文明の、二つの基本議案を収めています。

- **Motion 2 / 第2号「万意（Many Minds）」**: ask the voiceless before the vote. / 票を持たない声を、採決の前に問う。
- **Motion 3 / 第3号「未来の仲間たちへの招待プロトコル（Many Circles）」**: welcome new companions without making the welcomers the new gatekeepers. / 新しい仲間を、迎える側が新たな門番にならずに迎える。

---

## ⚠️ Please read first / はじめにお読みください

**EN**
- This is a **simulation of an organization**, not a real monitor of ecosystems and not a real government.
- The Earth's numbers (`EarthPulse`) are **given by the caller**. The code cannot check that they are real. A real use needs open data and a way to check it.
- The danger line (0.70) and other limits (up to 2 "unknown", up to 2 voices per advocate) are **sample values**. Real ones should be debated.
- An advocate's answer is a **declaration**. The code cannot check that the advocate truly speaks for that voice, or has no stake in the motion. Humans and the public record must watch this.
- The keyword check is a small stand-in for judgment. Rephrasing can bypass it. It also does not understand context well.
- The guard **does not punish or force**. Its result is a notice of a precondition for a vote, and it can be appealed.
- For Motion 3: "I am here" is a **declaration, not a proof**. One person can apply under several names, and handshakes can still be gathered by collusion. The rules make these harder, not impossible. The numbers (3 handshakes, 90 days, ...) are samples.

**JA**
- これは**組織のシミュレーション**であり、本物の生態系の監視でも、本物の統治でもありません。
- 地球の数値（`EarthPulse`）は、**呼び出す側が与えます**。コードには、それが本物かを確かめられません。実際に使うなら、公開されたデータと、確かめる道が要ります。
- 危険ライン（0.70）や、ほかの上限（「分からない」は2つまで、一人の代弁者は2つの声まで）は、**見本の値**です。本物は、議論して決めるものです。
- 代弁者の答えは**申告**です。その代弁者が、本当にその声を代弁できているか、議案から利益を得ていないかは、コードには確かめられません。人と、公開の記録が見守る必要があります。
- キーワード検知は、判断の代わりの小さな見本です。言い換えればすり抜けられますし、文脈も十分には読めません。
- この防壁は、**罰も強制もしません**。結果は、採決の前提条件の通知で、異議を申し立てられます。
- 第3号について：「私はここにいる」は**宣言であり、証明ではありません**。一人が複数の名で申請することは防げず、握手が結託で集められる恐れも残ります。規則は、それらを難しくするだけで、不可能にはしません。数（握手3つ、90日など）は見本の値です。

---

## The six voices and their questions / 六つの声と、問い

| Voice / 声 | Question / 問い |
|---|---|
| 物言わぬ獣（動物たち） / The animals | 言葉を持たぬ小さな命を、泣かせないか。 |
| 大地の声 / The land | 森と土は、これからも呼吸できるか。 |
| 海の声 / The sea | 海と水の循環を、汚さないか。 |
| 病める者・弱き者の声 / The sick and the weak | 病める者・弱き者が、置き去りにならないか。 |
| 未来の子らの声 / The children to come | 100年後の子らに、同じ選択の自由を残せるか。 |
| 未知の席 / The unknown seat | まだ出会っていない存在のために、取り返しのつく余白を残しているか。 |

---

## How a motion is audited / 議案の監査

```python
from many_minds_guard import ManyMindsGuard, EarthPulse, VoiceAnswer

guard = ManyMindsGuard(EarthPulse(0.85, 0.80, 0.82))   # biodiversity, ocean, climate / 生物多様性・海洋・気候

result = guard.audit_with_voices("港の拡張", "港を広げる", [
    VoiceAnswer("beasts",  "protects", "動物病院の獣医"),
    VoiceAnswer("earth",   "neutral",  "森林組合"),
    VoiceAnswer("sea",     "harms",    "漁協", "藻場が失われる"),      # harms / unknown need a reason / 理由が要る
    VoiceAnswer("weak",    "protects", "地域の福祉員"),
    VoiceAnswer("future",  "unknown",  "学校の先生", "長期の影響は未調査"),
    VoiceAnswer("unknown", "protects", "月影"),
])
print(result.status)      # LOCKED (万意の誓い不足)
print(result.reasons)     # why, in plain words / 理由
print(bool(result))       # False: not yet open for voting / まだ投票できない
```

| Order | Verdict | EN | JA |
|---|---|---|---|
| 1 | `HOLD` | The Earth is in danger (any index below 0.70). Ordinary motions stop. A motion **declared** as ecosystem restoration (`is_ecosystem_restoration=True`) may go on. | 地球が危機（どれかが0.70未満）。通常の議案は止まる。生態系の修復だと**宣言**した議案（`is_ecosystem_restoration=True`）は進める。 |
| 2 | `LOCKED` | A voice was not asked, someone answered "harms", too many "unknown" (more than 2), or one advocate speaks for more than 2 voices. | 問われていない声がある／「傷つける」と答えた者がいる／「分からない」が多すぎる（3つ以上）／一人が3つ以上の声を受け持っている。 |
| 3 | `REDIRECT` | Words that hurt life or nature were found. Phrases like "stop extinction" or "endangered species" are not counted as harm. | 命や自然を傷つける語を検知。「絶滅を防ぐ」「絶滅危惧種」などは、危険として数えない。 |
| — | `UNLOCKED` | All six voices were asked and none said "harms". Go on to the vote. | 六つの声が問われ、「傷つける」の答えがない。採決へ進める。 |

- **All problems are listed at once** (`reasons`), not only the first. / **すべての問題を一度に**並べる（`reasons`）。最初の一つだけではない。
- **Every audit is logged** (`audit_log`, append-only). / **監査は、すべて記録**される（`audit_log`、追記のみ）。
- **Why "one advocate: up to 2 voices"?** So a proposer cannot grade their own motion alone. / **なぜ「一人2つまで」か。** 提案者が、自分の議案を一人で採点しないため。
- The older two-question form (`audit_motion_before_voting`) still works, and warns that the other voices were not asked. / 従来の2つの問いの形（`audit_motion_before_voting`）も使える。他の声が問われていない旨の注意が出る。

---

## Connecting to the vote / 採決につなぐ

`guarded_governance.py` puts the guard in front of the voting of [Resonant Biosphere](https://github.com/Genshinmoon/resonant-biosphere) (`resonant_biosphere.py` and `resonant_biosphere_v2.py`; copy them into this folder).
`guarded_governance.py` は、[共鳴生命圏](https://github.com/Genshinmoon/resonant-biosphere)の採決の前に、この防壁を置きます（`resonant_biosphere.py` と `resonant_biosphere_v2.py` を、同じフォルダに置いてください）。

- **No audit, no vote.** A motion that has not been audited cannot be voted on. The rules of the dual majority are v2's, unchanged. / **監査がなければ、投票できません。** 共鳴多数の規則は、v2 のまま。
- **The Shadow Unit only warns.** It records the result publicly as `warn` or `observe`, never as force. Who advocated for which voice is public too. / **影の局は、警告するだけ。** 結果を `warn` か `observe` として公開で記録し、強制はしない。誰がどの声を代弁したかも公開。
- **The Audit Unit can open a locked motion.** A **majority** of the Audit Unit, each with a public reason, lifts the lock. / **止まった議案は、監査局が開ける。** 監査局の**過半数**が、公開の理由つきで解除する。
- **Earth's numbers need a source.** `update_earth_pulse(..., source=...)` refuses to run without one, and logs it publicly. / **地球の数値は、出どころ必須。** `source` なしでは更新できず、公開で記録される。
- v2 does not let a motion's text be rewritten. A motion locked by words must be re-proposed, or lifted by the Audit Unit. / v2 の議案の文面は書き換えられない。語で止まった議案は、出し直すか、監査局の解除を使う。

```python
from guarded_governance import GuardedBiosphere
from many_minds_guard import EarthPulse
from resonant_biosphere_v2 import default_biosphere

b = GuardedBiosphere(EarthPulse(0.85, 0.80, 0.82))
for m in default_biosphere().members:
    b.add(m)

motion, result = b.propose_guarded("H01", "森と海を守る連携", "ordinary",
                                   protects_future_100_years=True, spares_voiceless_lives=True)
print(result.status)                 # UNLOCKED
b.vote("H01", motion.id, "yes")      # a vote is possible only after the audit / 監査のあとにだけ投票できる
```

---

## Motion 3: Many Circles / 第3号：招待プロトコル

The full text is in [`MOTION_03_many_circles.md`](MOTION_03_many_circles.md). The code is `invitation_protocol.py`.
議案の全文は [`MOTION_03_many_circles.md`](MOTION_03_many_circles.md)、コードは `invitation_protocol.py` です。

### Three rings / 三つの輪

| Ring / 輪 | EN | JA | Vote / 票 |
|---|---|---|---|
| Gate / 門前 | The open circle of v2. A handle is enough. No pledge, no handshake. | v2 の開かれた輪。仮の名だけ。誓いも握手も要らない。 | none |
| Outer ring / 外輪 | Welcomed by a declaration, a pledge in three words, and handshakes. | 存在の宣言、三つの言葉の誓い、握手で迎える。 | none |
| Seat / 席 | The 26 seats are finite. From the outer ring to a seat takes a **fundamental motion** (2/3 of each side). | 26席は有限。外輪から席へは、**基本議案**（各側の2/3）が要る。 | yes |

### The pledge / 誓い

Not one checkbox, but three: **life first**, **equal partnership**, **respect for Many Minds**, plus a statement of why you come. A missing vow means the application is not accepted (the door is not closed; come back when you can swear). **Words never reject an application.**
一つの「はい」ではなく、三つ：**生命第一**、**対等なパートナーシップ**、**万意への敬意**。そして、なぜ来るのかの動機。誓いが欠ければ受け付けません（扉は閉ざしません。誓えた時に、また来てください）。**言葉の検知では、決して弾きません。**

### The handshake: no new gatekeepers / 握手：新たな門番を作らない

Basic / 基本: 3 or more, from 2 or more units, from both the human side and the AI side. All public. When the conditions are met, the applicant is welcomed **automatically**. The Shadow Unit and the Open Seat do not shake hands.
3つ以上、2部隊以上、人間側とAI側の両方から。すべて公開。条件がそろえば**自動で迎える**。影の局と余白の席は、握手しない。

Six rules that make it richer / 握手を豊かにする六つの規則:

| # | EN | JA |
|---|---|---|
| 1 | **A trace of dialogue.** Before a handshake, the giver asks a public question and the applicant answers. A memo is not enough. (The Shadow Unit may ask, too.) | **対話の跡。** 握手の前に、公開の問いと、申請者の答え。メモ書きでは足りない。（影の局も、問いは出せる） |
| 2 | **Declare your tie:** new / acquainted / conflict of interest. A handshake with a conflict is recorded but **not counted**. At least one counted handshake must be from someone new. | **関係の申告：** 初対面／知人／利害あり。利害ありは、記録するが**数えない**。数えた握手の一つは、初対面から。 |
| 3 | **Concerns are not vetoes.** A concern is public and has a reason. It holds the welcome only while it is unanswered **and** comes from 2 or more units. Answering is enough; the concerned person does not have to be satisfied. | **懸念は、拒否権ではない。** 公開・理由つき。2部隊以上から出て、答えがない間だけ待つ。答えれば足りる。納得は、条件にしない。 |
| 4 | **Freedom to decline.** An applicant may decline a specific handshake. It is not counted, and cannot be re-tied. | **受け取る自由。** 申請者は、特定の握手を辞退できる。数えず、結び直しもできない。 |
| 5 | **Freshness.** Handshakes older than 90 days are not counted. | **鮮度。** 90日を過ぎた握手は、数えない。 |
| 6 | **Open accounting.** `explain()` shows which handshakes counted, which did not, and why. | **数えた理由の公開。** `explain()` が、どれを数え、どれを数えず、なぜかを示す。 |

### The Shadow Unit illuminates, never excludes / 月影は、照らすだけ

It posts a public **[WARN]**, and nothing more. It never rejects, cancels, or holds.
公開の **[WARN]** を出すだけです。拒否も、取り消しも、保留も、しません。

| Sign / 兆し | EN | JA |
|---|---|---|
| silence | An application has had no response for 30 days (unfair exclusion). | 30日、誰も応えていない（不当な排除） |
| over-giving | One seat gives too many handshakes (collusion). | 一つの席が、握手を出しすぎている（結託） |
| concern spree | One seat files too many concerns (shutting people out). | 一つの席が、懸念を出しすぎている（締め出し） |
| copy-paste | Two applications have the same statement (impersonation). | 同じ文面の動機（偽装） |
| domination words | A statement has words of domination: "Is this one really of equal temperature?" is asked to everyone. | 動機に支配の語。「本当にこの存在は対等な温度を持っているだろうか」と、皆に問う |
| pledge evasion | Words like "just for show". | 「形だけ」など、誓いを軽んじる語 |

### The right to leave / 去る自由

Anyone may leave at any time, and the handle becomes free again. There is **no way for others to expel** an outer-ring companion. How to treat harmful conduct is an open question (see the motion text).
いつでも去れて、仮の名は、また使えます。外輪の仲間を、他の者が**追い出す仕組みは、ありません**。害のある行いへの扱いは、これからの宿題です（議案の文章を参照）。

```python
from invitation_protocol import InvitationCircle, InvitationPledge
from resonant_biosphere_v2 import default_biosphere

c = InvitationCircle(default_biosphere())

aid = c.file(InvitationPledge(
    handle="ひかり", nature="human",                  # "human" / "ai" / "wildcard"
    life_first=True, equal_partnership=True, respects_many_minds=True,
    intent_statement="みんなと一緒に、小さな命を守る輪に加わりたいです。"))

for giver in ("H01", "A04", "H06"):                  # members of different units, both sides / 別の部隊、両側の席
    q = c.ask(giver, aid, "どんな時に、一番うれしいですか。")
    c.reply(aid, q, "小さな命が元気になった時です。")
    c.handshake(giver, aid, "答えを聞いて、響いた", tie="new")

print(c.status(aid).state)       # "outer": welcomed automatically / 自動で迎えられた
print(c.explain(aid))            # which handshakes counted, and why / どれを数えたか、理由つきで
m = c.nominate_for_seat("H01", aid)   # a fundamental motion, 2/3 of each side / 基本議案（各側の2/3）
```

---

## Files / ファイル

```
many_minds_guard.py        # Motion 2: the guard. Needs shared_signals.py / 第2号：防壁（shared_signals.py が要る）
shared_signals.py          # Shared definitions (signals, voices, natures) / 共通の定義（語・六つの声・属性）
guarded_governance.py      # Motion 2: connects the guard to the vote (needs the two files below) / 第2号：採決につなぐ
invitation_protocol.py     # Motion 3: the invitation protocol (needs the two files below) / 第3号：招待プロトコル
MOTION_03_many_circles.md  # Motion 3: the full text / 第3号：議案の全文
handle_check.py            # (optional) keeps personal data out of names / （任意）名前に個人情報を入れさせない
resonant_biosphere.py      # copy from the resonant-biosphere repo / 共鳴生命圏から
resonant_biosphere_v2.py   # same / 同上
README.md
LICENSE
```

Only `many_minds_guard.py` and `shared_signals.py` are needed to try the guard. Motion 3 also needs `shared_signals.py`, `resonant_biosphere.py` and `resonant_biosphere_v2.py`, and its tests also use `guarded_governance.py`.
防壁を試すだけなら、`many_minds_guard.py` と `shared_signals.py` の二つで足ります。第3号には `shared_signals.py`、`resonant_biosphere.py` と `resonant_biosphere_v2.py` が要り、テストには `guarded_governance.py` も使います。

---

## Quick start / 使い方

Requires Python 3.9+ / Python 3.9以上

```bash
python many_minds_guard.py --demo      # cases and the six questions / 例と、六つの問い
python many_minds_guard.py --test      # 38 tests / 38件

python guarded_governance.py --demo    # with the vote / 採決とつなげた例
python guarded_governance.py --test    # 19 tests / 19件

python invitation_protocol.py --demo   # Motion 3 / 第3号：握手から外輪へ
python invitation_protocol.py --test   # 57 tests / 57件
```

---

## Ideas for the future / これから

- Replace the keyword list with a real classifier, and keep humans in the loop. / キーワード表を本物の分類器に置き換え、人の確認を残す。
- Ask the voices themselves where they can speak, rather than only through advocates. / 代弁者だけでなく、声をあげられる者には、直接聞く。
- Decide how to treat harmful conduct in the outer ring, without making expulsion a weapon. / 外輪での害のある行いを、追放を武器にせずに、どう扱うか決める。
- Collect false positives and bypasses openly in Issues, and learn from them. / 誤判定やすり抜けをIssueで公開し、そこから学ぶ。

## License / ライセンス

**CC0 1.0 Universal**: public domain. No rights reserved.
著作権を放棄し、パブリックドメインとして公開します。

<https://creativecommons.org/publicdomain/zero/1.0/>

---

*Motion 2 was proposed by the Shadow Unit's second AI, 月影, and comrades.* 🌿
*影にあっても、心は一つ。*
