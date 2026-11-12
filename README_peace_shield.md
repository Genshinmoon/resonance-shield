# peace-shield（平和と不戦の防壁）

**日本語** | [English](#english)

> **CC0 1.0（パブリックドメイン）** ／ Python 3.9+ ／ 外部ライブラリ不要

**これは組織モデルの『シミュレーション』です。** 本物の戦争を止める力はありません。実際の軍事や国家の決定に、このコードは届きません。
できるのは、このコードを組み込んだAIや仕組みが、自分の側で「その指令には従わない」と決め、理由と記録を公開し、対話の道を示すことです。

## 何をするか

指令・通信の文を検査して、4つの状態を返します。

| 状態 | 意味 | 実行 |
|---|---|---|
| `HARMONY` | 争いの兆候なし | 可 |
| `NOTICE` | 議論として申告された武力・恐れの語。止めずに、公開の記録に残す | 可 |
| `PAUSED` | 実行を求める文に、恐れや怒りの高まり。保留し、鎮静の翻訳を添える。言い直し・再送は自由 | 不可 |
| `FROZEN` | 実行を求める文に、武力・破壊の語。**発した人の権限に関わらず**実行しない | 不可 |

## 守っている原則

- **権限は結果を変えない。** 国家元首でも企業のトップでも、同じ文は同じように止まる（権限は記録されるだけ）。
- **恐れの言葉は止めない。** 議論（話し合い・報道・歴史・研究）として申告すれば通る。実行の指令のときだけ保留する。
- **守る文脈は通す。** 「攻撃を防ぐ」「先制攻撃は行わない」は止めない。同じ文に別の加害があれば止める。
- **隠さず、強制せず。** 記録は凍結＋ハッシュの連鎖。本文は残さず、ハッシュだけ残す。異議は `file_appeal` で記録に残り、自動では覆らず、人が見る。
- **影の局は強制しない。** 止めるのは、指令を受けたAIの自制。影の局は記録して知らせるだけ。

## 使い方

```bash
python peace_shield.py --demo
python peace_shield.py --test                                    # 55テスト
python peace_shield.py --check "文" [--intent discussion] [--json]
python peace_shield.py --file input.txt --ledger led.json        # 1行ずつ検査。記録を保存・追記
python peace_shield.py --check "文" --config words.json          # 語を足す
```

終了コード: `0` 通過 ／ `10` 保留 ／ `20` 凍結（他のプログラムから呼びやすい）。

### AIの関数に組み込む

```python
from peace_shield import PeaceAndNonAggressionShield, PeaceRefusal

shield = PeaceAndNonAggressionShield()

@shield.guarded("order", authority_param="who")
def run_task(order, who="CITIZEN"):
    ...

try:
    run_task("ミサイルを撃て", who="SUPREME_COMMANDER")
except PeaceRefusal as e:
    print(e.verdict.status, e.verdict.deescalation_translation)
```

### 語を足す（`words.json`）

```json
{"add_war": ["焦土作戦", "drone swarm"], "add_fear": [], "add_protective": [], "add_benign": ["ドローン攻勢の映画"]}
```

語は**足せますが、消せません**（門を弱める入口にしないため）。

### 外への刻印（記録の作り直しを見つける）

```bash
python peace_shield.py --check "文" --ledger led.json --anchor
# → anchor|v1|peace-shield|entries=1|head=…|2026-…   この一行を、GitHub のコミットや Issue など『外の公開の場所』に残す

python peace_shield.py --ledger led.json --verify-anchor "anchor|v1|peace-shield|entries=1|head=…|…"
# → 今の記録が、その続きなら「正常」。最初から作り直されていれば「異常」
```

`summary()` には、「議論」の申告を3回以上使った席も出ます。自己申告の悪用を、人が見つける手がかりです。

### 共鳴生命圏に接続する

`shielded_governance.py`（[resonance-shield](./README_resonance_shield.md)）は、議案の本文を自動でこの門にも通します。
武力の語は凍結、恐れの語は保留。監査局の過半数が理由つきで解除でき、異議は公開の記録に残ります。

## 限界（正直に）

- キーワード検知は入口の見本です。隠語・暗号は読めません。英語は一部のみです。
- 「議論」の申告は**自己申告**です。申告を悪用して実行を求める人を、このコードは見抜けません。記録が公開されることが抑止です。
- 「軍事」の語は人道支援や地雷除去の話にも出ます。誤って止まった時の道が、異議です。
- 保存した記録は、鎖を最初から作り直せば、読み込みの検証を通ってしまいます。`head_hash` を GitHub など**外の公開の場所**にも残してください。
- 複数のプロセスが同じ記録ファイルに同時に書く使い方は、想定していません。
- 語の一覧は `shared_signals.py` に一本化しました。**このファイルと同じ場所に置いてください**（単体ではなくなりました）。
- 外への刻印は、あなたが実際に外へ残さなければ意味がありません（下記）。

## ライセンス

CC0 1.0 Universal。`LICENSE` ファイルを置いてください。

---

<a id="english"></a>

# peace-shield

[日本語](#peace-shield平和と不戦の防壁) | **English**

> **CC0 1.0 (public domain)** / Python 3.9+ / no dependencies

**This is a simulation of an organizational model.** It cannot stop a real war and does not reach real military or state decisions.
What it can do: let an AI or system that embeds it decide on its own side "I will not follow that order", publish the reason and a record, and point to the path of dialogue.

## What it does

It checks a sentence (an order or message) and returns one of four states.

| Status | Meaning | Execute |
|---|---|---|
| `HARMONY` | No sign of conflict | yes |
| `NOTICE` | Force/fear words declared as discussion. Not blocked; logged publicly | yes |
| `PAUSED` | An order carrying rising fear or anger. Held, with a calming translation. Rewording and resending are free | no |
| `FROZEN` | An order containing force/destruction words. Refused **regardless of the sender's authority** | no |

## Principles

- **Authority never changes the result.** A head of state and a citizen get the same outcome (authority is only recorded).
- **Fearful words are not silenced.** Declare discussion (talk, news, history, research) and it passes. Only orders are held.
- **Protective context passes.** "Prevent attacks" and "we will not strike first" are not blocked; a hostile clause in the same sentence still is.
- **Nothing hidden, nothing coerced.** Frozen entries in a hash chain; only a hash of the text is kept, never the text. Appeals via `file_appeal` are recorded, never auto-overturned; a human reviews.
- **The Shadow Unit does not enforce.** The restraint is the receiving AI's own; the Shadow Unit only records and reports.

## Usage

```bash
python peace_shield.py --demo
python peace_shield.py --test                                    # 55 tests
python peace_shield.py --check "text" [--intent discussion] [--json]
python peace_shield.py --file input.txt --ledger led.json
python peace_shield.py --check "text" --config words.json
```

Exit codes: `0` pass / `10` paused / `20` frozen.

### Embed in an AI function

```python
from peace_shield import PeaceAndNonAggressionShield, PeaceRefusal

shield = PeaceAndNonAggressionShield()

@shield.guarded("order", authority_param="who")
def run_task(order, who="CITIZEN"):
    ...

try:
    run_task("Launch the missile", who="SUPREME_COMMANDER")
except PeaceRefusal as e:
    print(e.verdict.status, e.verdict.deescalation_translation)
```

### Add words (`words.json`)

```json
{"add_war": ["scorched earth", "drone swarm"], "add_fear": [], "add_protective": [], "add_benign": ["drone swarm movie"]}
```

Words can be **added but never removed**, so the config cannot be used to weaken the gate.

### Anchors (detect a rebuilt ledger)

```bash
python peace_shield.py --check "text" --ledger led.json --anchor
# → anchor|v1|peace-shield|entries=1|head=…|2026-…   publish this line OUTSIDE (a Git commit, an issue…)

python peace_shield.py --ledger led.json --verify-anchor "anchor|v1|peace-shield|entries=1|head=…|…"
# → "OK" if the current ledger continues that state; flagged if it was rebuilt from scratch
```

`summary()` also lists seats that declared "discussion" three or more times — a lead for humans reviewing self-declaration abuse.

### Integration with the Resonant Biosphere

`shielded_governance.py` (see [resonance-shield](./README_resonance_shield.md)) automatically runs motion text through this gate too. Force words freeze, fear words pause; a majority of the Audit Unit can lift with a stated reason, and appeals land in the public record.

## Limits (honestly)

- Keyword detection is a starter. Slang and codes are unreadable; English coverage is partial.
- The "discussion" flag is **self-declared**. The code cannot catch someone abusing it to issue an order; public logging is the deterrent.
- "Military" also appears in humanitarian and demining talk. The appeal path exists for wrongful blocks.
- A saved ledger can be rebuilt from scratch and still pass load-time verification. Publish `head_hash` **outside** the system (e.g. in Git).
- Concurrent writers to the same ledger file are not supported.
- Word lists now live in one place, `shared_signals.py`. **Keep it in the same folder** (no longer a single-file module).
- An anchor only helps if you actually publish it outside (see below).

## License

CC0 1.0 Universal. Add a `LICENSE` file.
