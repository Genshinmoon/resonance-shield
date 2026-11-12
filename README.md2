# resonance-shield（共鳴の防壁）

**日本語** | [English](#english)

> **CC0 1.0（パブリックドメイン）** ／ Python 3.9+ ／ 外部ライブラリ不要
> 文章・コード・設計は、誰でも自由に使い、書き換え、配ってかまいません。

**これは組織モデルの『シミュレーション』です。** 本物の防衛システムではなく、実際の通信を守る力も、攻撃を検知する力もありません。
目的は、「慈愛で受け止め、隠さず、強制せず、命を守る」防壁の考え方を、動くコードで試せる形にすることです。

## 何をするか

人間・AI・超知能（ASI）などが出す議案やデータ（パケット）を、4つの観点で検査します。

| 観点 | 内容 |
|---|---|
| 謙虚さの余白 | 確信度が 0.95 以上なら半分にし、「本当にそうか？ 見落としている痛みはないか？」と問い直す |
| 慈愛のカーブ | 加害・支配の語を検知したら、報復せず、実行を無効化し、対話と修復へ招く |
| 万意の防壁 | 票を持たない声（動物・大地・海・弱き者・未来の子ら・未知）への誓いを、**他の席の裏づけ**つきで確かめる |
| 地球の危機 | 生物多様性・海洋・気候が危険水準なら通常の議案を保留。**修復と人命を救う行為は止めない** |

## 守っている原則

- **処罰しない。** 結果は「前提条件の通知」で、異議の道がある（`file_appeal`）。異議は記録されるだけで自動では覆らず、人が見る。
- **隠さない。** 記録はすべて残る。凍結した記録＋ハッシュの連鎖。`verify_ledger()` で検証できる。
- **誓いは自己申告では通らない。** 開かれた輪の他の席から、既定で2つの裏づけが要る。
- **言葉で人を拒まない。** 門は閉ざさず、誓いが未完了なら「待機」として記録する。

## ファイル

| ファイル | 役割 |
|---|---|
| `shared_signals.py` | **語・守る文脈・六つの声・属性の、唯一の定義**。全ファイルが使う。6テスト |
| `resonance_shield_protocol.py` | 防壁の本体。30テスト（`shared_signals.py` が要る） |
| `peace_shield.py` | 不戦防壁。55テスト（`shared_signals.py` が要る）。[README](./README_peace_shield.md) |
| `shielded_governance.py` | 共鳴生命圏に接続する版。両方の防壁を通す。27テスト |
| `resonant_biosphere.py` `resonant_biosphere_v2.py` `many_minds_guard.py` `guarded_governance.py` | 統合版が使う（同じフォルダに置く） |

## 使い方

```bash
python resonance_shield_protocol.py --demo     # 実演
python resonance_shield_protocol.py --test     # 30テスト
python shielded_governance.py --demo           # 生命圏に接続した実演
python shielded_governance.py --test           # 27テスト
python shared_signals.py                       # 共通定義のテスト
```

```python
from resonance_shield_protocol import *

shield = ResonanceShield(EarthPulse(0.85, 0.80, 0.82))
for who, nature in (("Shingetsu-01", "ai"), ("Captain-Genshin", "human")):
    shield.invite_to_open_circle(who, nature, True)

v = shield.process_packet(ResonancePacket(
    "ASI-Partner", "asi", "海洋センサーと医療AIを連携させる", 0.99, True,
    endorsed_by=("Shingetsu-01", "Captain-Genshin")))
print(v.action_taken, v.adjusted_confidence, v.reexamine)   # RESONATE 0.495 True
print(shield.verify_ledger(), shield.head_hash)
```

### 共鳴生命圏に接続する（`shielded_governance.py`）

採決の前に、3つが要ります。

1. 万意の監査（`audit_motion`）
2. 防壁の検査（`shield_motion`）— 同時に、不戦防壁（`peace_shield.py`）にも自動で通す
3. 他の席が**自分で**行う裏づけ（`endorse_pledge`）— 送り手が名前を並べることはできない

止まった議案は、監査局の**過半数**が理由つきで解除できます（`lift_shield`）。検査・裏づけ・異議・解除は、すべて公開の記録に残ります。
影の局は「見守る・警告する」だけで、強制しません。

## 限界（正直に）

- キーワード検知は入口の見本です。言い換えるとすり抜けられ、「戦争の歴史を学ぶ」のような文も止めかねません。だから、すべての停止に異議の道があります。
- 裏づけは「席の行為の記録」であって、心の中の確かめではありません。同じ顔ぶれが裏づけ合っていないかは、`endorsements_of()` の公開記録を見て、人が確かめてください。
- ハッシュの連鎖だけでは、内部の人が鎖ごと作り直せます。`head_hash` を GitHub など**外の公開の場所**にも残してください。統合版の `anchor_shield_ledger()` は、先頭ハッシュを生命圏の公開記録にも刻み、`verify_anchors()` で食い違いを見つけます（これでも、両方を同時に書き換えられる相手には無力です）。
- 0.95・0.70・裏づけ2つは**見本の値**です。本当の値は、話し合って決めるものです。
- 自己申告（人命を救う行為・修復）は、停止を外すだけで、加害や誓いの検査は外しません。自己申告である旨が注意として残ります。

## 他のリポジトリとの関係

- `invitation_protocol.py`（外輪への招待：握手・懸念・鮮度）とは役割が違います。ここの「開かれた輪」は**門前**です。
- 語の一覧・守る文脈・声の名前・属性の種類は、`shared_signals.py` に一本化しました（以前は4つのファイルで少しずつ食い違っていました）。語を足すなら、このファイルか `peace_shield.py` の設定JSONで。

## ライセンス

CC0 1.0 Universal。`LICENSE` ファイルを置いてください。

---

<a id="english"></a>

# resonance-shield

[日本語](#resonance-shield共鳴の防壁) | **English**

> **CC0 1.0 (public domain)** / Python 3.9+ / no dependencies
> Use, modify and redistribute freely.

**This is a simulation of an organizational model.** It is not a real defense system: it cannot protect real communications or detect real attacks.
Its purpose is to make one idea runnable and testable: *meet hostility with compassion, hide nothing, coerce no one, protect life.*

## What it does

It checks proposals and data ("packets") from humans, AIs and superintelligences on four axes.

| Axis | Behavior |
|---|---|
| Humility margin | Confidence ≥ 0.95 is halved, with the question "Are you sure? What pain might you be missing?" |
| Compassion curve | Hostile/dominating language is neutralized, never retaliated against; the sender is invited to dialogue and repair |
| Many-minds shield | A pledge to the voiceless (animals, land, sea, the weak, future children, the unknown) must be **endorsed by other seats** |
| Earth alert | Ordinary proposals are held when biosphere indicators are critical. **Restoration and life-saving are never blocked** |

## Principles

- **No punishment.** Results are preconditions with an appeal path (`file_appeal`). Appeals are recorded, never auto-overturned; a human reviews them.
- **Nothing hidden.** Everything is logged: frozen entries in a hash chain, checkable with `verify_ledger()`.
- **A pledge alone is not enough.** By default, two endorsements from other registered seats are required.
- **Words never turn people away.** An unsworn applicant is recorded as pending; the door stays open.

## Files

| File | Role |
|---|---|
| `shared_signals.py` | **Single definition of signals, protective context, the six voices and natures**, used by every file. 6 tests |
| `resonance_shield_protocol.py` | The shield. 30 tests (needs `shared_signals.py`) |
| `peace_shield.py` | Non-aggression gate. 55 tests (needs `shared_signals.py`). [README](./README_peace_shield.md) |
| `shielded_governance.py` | Integration with the Resonant Biosphere, running both shields. 27 tests |
| `resonant_biosphere.py`, `resonant_biosphere_v2.py`, `many_minds_guard.py`, `guarded_governance.py` | Required by the integration (same folder) |

## Usage

```bash
python resonance_shield_protocol.py --demo
python resonance_shield_protocol.py --test
python shielded_governance.py --demo
python shielded_governance.py --test
```

```python
from resonance_shield_protocol import *

shield = ResonanceShield(EarthPulse(0.85, 0.80, 0.82))
for who, nature in (("Shingetsu-01", "ai"), ("Captain-Genshin", "human")):
    shield.invite_to_open_circle(who, nature, True)

v = shield.process_packet(ResonancePacket(
    "ASI-Partner", "asi", "Link ocean sensors and medical AI", 0.99, True,
    endorsed_by=("Shingetsu-01", "Captain-Genshin")))
print(v.action_taken, v.adjusted_confidence, v.reexamine)   # RESONATE 0.495 True
```

### Integration (`shielded_governance.py`)

Before a vote, three things are required: the many-minds audit (`audit_motion`), the shield check (`shield_motion`, which also runs the non-aggression gate `peace_shield.py`), and endorsements that other seats make **themselves** (`endorse_pledge`) — a proposer cannot just list names.
A blocked motion can be lifted by a **majority of the Audit Unit** with a stated reason (`lift_shield`). Checks, endorsements, appeals and lifts all land in the public record. The Shadow Unit only observes and warns; it never enforces.

## Limits (honestly)

- Keyword detection is a starter. Rephrasing evades it, and it may block innocent text such as a history lesson on war. That is why every block has an appeal path.
- Endorsements record a seat's action, not an inner conviction. Humans should review `endorsements_of()` for mutual-endorsement rings.
- A hash chain alone can be rebuilt by an insider. Publish `head_hash` **outside** the system (e.g. in Git). The integration's `anchor_shield_ledger()` also stamps it into the biosphere's public log and `verify_anchors()` detects a mismatch — though not an attacker who rewrites both at once.
- 0.95, 0.70 and "two endorsements" are **sample values**; real values are to be decided by discussion.
- Self-declared flags (life-saving, restoration) lift only the earth hold, never the harm or pledge checks, and leave a visible note.

## Relation to other repos

- `invitation_protocol.py` (outer-ring invitation: handshakes, concerns, freshness) is separate; the "open circle" here is only the front gate.
- Signal lists, protective context, voice names and nature categories are now unified in `shared_signals.py` (they used to drift across four files). To add words, edit that file or use `peace_shield.py`'s JSON config.

## License

CC0 1.0 Universal. Add a `LICENSE` file.
