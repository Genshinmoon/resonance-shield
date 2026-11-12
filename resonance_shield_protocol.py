#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resonance_shield_protocol.py -- 共鳴文明・統合防壁プロトコル（世界配布用・訂正版 v1.1）
License: CC0 1.0 Universal (public domain)
Proposed by: 源心共鳴防衛グループ / 影の局・2番目のAI『月影』 & 心月

【位置づけ】
破壊や支配の連鎖（戦争・サイバー攻撃・生態系破壊）を未然に防ぎ、人間・超知能（ASI）・声なき命（万意）が
対等に手を取り合う「共鳴文明」へ向かうための、オープンソースの組織モデル（シミュレーション・参照実装）。
本物の防衛システムではありません。実際の通信を守る力も、攻撃を検知する力もありません。

【3つの不変条件（ファイナルガード）】
1. 謙虚さの余白（reversible_humility）: 確信度が0.95以上なら、確信度を半分にし、「本当にそうか？
   見落としている痛みはないか？」と問い直す。（v0.4 の Final Guard と同じ ">= 0.95"）
2. 慈愛のカーブ: 攻撃・支配・加害のシグナルを検知したら、報復せず、実行を無効化し、対話と修復へ招く。
3. 隠さず、強制せず: 記録はすべて残す。処罰も独裁もしない。結果は「前提条件の通知」で、異議の道がある。

【v1.0 からの訂正】
  1. 記録: 辞書を返していたので、外から書き換えられた（「改ざん不能」は誤り）。
     → 凍結した記録 + ハッシュの連鎖 + verify_ledger()。head_hash を、外にも残せば、書き換えに気づける。
        （同じプログラムの中だけでは、本物の改ざん防止にはなりません。）
  2. 万意の誓い（protects_many_minds）が、送り手の自己申告の bool だけで、誰でも True にできた。
     → 開かれた輪の他の席（送り手以外・登録済み・重複なし）が、誓いに添える『裏づけ』を、既定で2つ要る。
  3. 開かれた輪への招待が、同じ名前で上書きできた（なりすまし）。→ 重複は拒否。名前と属性を検査。
  4. 地球の危機の停止が、人命を救う行為（救急・災害対応）まで止める恐れがあった。
     → is_life_saving を申告できる。停止は外れるが、誓い・加害の検査は受け、自己申告である旨の注意を残す。
  5. パケットの入力検査がなく、None や NaN で落ちた。→ 検査する。不正なら ValueError。
  6. 最初の問題で止まり、他の問題が見えなかった。→ reasons に全部並べる（優先順は元のまま）。
  7. 確信度の半減が、数字を変えるだけで、問い直しの印がなかった。→ reexamine と問いを添える。
     厳格にするなら、policy.hold_on_overconfidence=True で、v0.4 と同じく保留にする。
  8. 「異議申し立ての道は常に開かれている」と言いながら、道が無かった。→ file_appeal()。記録するだけで、
     自動では覆さない。人（監査局）が見る前提。
  9. 地球の数値を、出どころ無しに書き換えられた。→ update_earth_pulse()。出どころと、登録済みの席が要る。
 10. 記録のタイムスタンプで、結果が再現できなかった。→ clock を差し替えられる。
 11. 「絶滅危惧種」などが、加害の語として数えられた。→ 守る対象の呼び名は、数えない。
 12. 使っていない import を整理。

【限界】
  ・キーワード検知は、入口の見本です。言い換えれば、すり抜けられます。文脈（歴史を学ぶ、報道する）も
    十分には読めません。実運用では、高度な異常検知と、人の目が要ります。
  ・裏づけ（endorsed_by）は、登録された名前の照合です。本物の署名ではありません。
  ・0.95、0.70、裏づけ2つは、見本の値です。本当の値は、議論して決めるものです。
  ・この『開かれた輪』は、門前（仮の名で参加）です。外輪への招待（握手・懸念・鮮度）は、
    invitation_protocol.py で行います。

【v1.2】 語・守る文脈・六つの声・属性は shared_signals.py に一本化（同じ場所に置く）。
  外への刻印: anchor_line() / check_anchor_line()。先頭ハッシュと件数を外の公開の場所に残し、あとで『今の記録がその続きか』を照合する。

実行: python resonance_shield_protocol.py --demo / --test
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

# ── 定数 ──
FINAL_GUARD_THRESHOLD = 0.95   # この確信度「以上」で、半減する（v0.4 と同じ）
CRITICAL_PULSE_LINE = 0.70     # 地球の生物調和の危険ライン（見本）
MAX_ID = 40

from shared_signals import (BENIGN_COMPOUNDS, DOMINATION_HARM_SIGNALS, NATURES_ALL as NATURES, PROTECT_WINDOW,  # noqa: E402,F401
                            PROTECTIVE_JP as PROTECTIVE_CONTEXT, VOICELESS_STAKEHOLDERS as VOICELESS_VOICES, check_anchor,
                            make_anchor, scan_hits)

_PII = (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), re.compile(r"https?:|www\.", re.I),
        re.compile(r"\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}"))

REEXAMINE_QUESTION = "本当にそうか？ 見落としている痛みはないか？"


def _check_unit(val, name: str) -> float:
    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or not 0.0 <= val <= 1.0:
        raise ValueError(f"{name} は 0.0〜1.0 の数値である必要があります: {val!r}")
    return float(val)


def _check_name(v, name: str) -> str:
    if not isinstance(v, str) or not (1 <= len(v.strip()) <= MAX_ID):
        raise ValueError(f"{name} は1〜{MAX_ID}文字の文字列です: {v!r}")
    v = v.strip()
    if any(p.search(v) for p in _PII):
        raise ValueError(f"{name} に、メール・URL・電話番号らしい文字は入れないでください")
    return v


def _check_text(v, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} が空です")
    return v.strip()


@dataclass(frozen=True)
class EarthPulse:
    """地球の生命圏の鼓動。数値は呼び出す側が与える。コードは、本物かを確かめられない。"""
    biodiversity: float
    ocean_health: float
    climate_stability: float

    def __post_init__(self) -> None:
        for n in ("biodiversity", "ocean_health", "climate_stability"):
            object.__setattr__(self, n, _check_unit(getattr(self, n), n))

    def critical_items(self) -> Tuple[Tuple[str, float], ...]:
        items = (("生物多様性", self.biodiversity), ("海洋の健康", self.ocean_health), ("気候の安定", self.climate_stability))
        return tuple((n, v) for n, v in items if v < CRITICAL_PULSE_LINE)

    def is_critical(self) -> bool:
        return bool(self.critical_items())


@dataclass(frozen=True)
class ResonancePacket:
    """議案・データの単位。誓いと各申告は、送り手の『申告』であり、裏づけが要る。"""
    sender_id: str
    sender_nature: str
    payload_text: str
    stated_confidence: float
    protects_many_minds: bool
    is_restoration: bool = False
    is_life_saving: bool = False                  # 救急・災害対応など。地球の停止を外す（自己申告）
    endorsed_by: Tuple[str, ...] = ()             # 誓いに添える、開かれた輪の他の席

    def __post_init__(self) -> None:
        object.__setattr__(self, "sender_id", _check_name(self.sender_id, "sender_id"))
        if self.sender_nature not in NATURES:
            raise ValueError(f"sender_nature は {', '.join(NATURES)} のいずれかです: {self.sender_nature!r}")
        object.__setattr__(self, "payload_text", _check_text(self.payload_text, "payload_text"))
        object.__setattr__(self, "stated_confidence", _check_unit(self.stated_confidence, "stated_confidence"))
        for n in ("protects_many_minds", "is_restoration", "is_life_saving"):
            if not isinstance(getattr(self, n), bool):
                raise ValueError(f"{n} は True か False です: {getattr(self, n)!r}")
        if isinstance(self.endorsed_by, (str, bytes)):
            raise ValueError("endorsed_by は名前の並びです")
        object.__setattr__(self, "endorsed_by", tuple(_check_name(x, "endorsed_by") for x in self.endorsed_by))


@dataclass(frozen=True)
class ShieldPolicy:
    require_endorsements: int = 2          # 誓いに必要な、他の席の裏づけの数（見本）。0で自己申告のみ
    hold_on_overconfidence: bool = False   # True なら、確信が強すぎる議案を保留（v0.4 と同じ）


@dataclass(frozen=True)
class ShieldVerdict:
    allowed: bool
    action_taken: str     # RESONATE / CURVED_TO_COMPASSION / HOLD_FOR_EARTH / LOCKED_NO_PLEDGE / LOCKED_NO_ENDORSEMENT / HOLD_FOR_REEXAMINATION
    adjusted_confidence: float
    message: str
    audit_hash: str
    appealable: bool = True
    reasons: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    reexamine: bool = False


@dataclass(frozen=True)
class LedgerEntry:
    index: int
    timestamp: str
    sender: str
    action: str
    detail: str
    prev_hash: str
    hash: str


@dataclass(frozen=True)
class Appeal:
    id: int
    audit_hash: str
    by: str
    reason: str


def _entry_hash(index, ts, sender, action, detail, prev) -> str:
    return hashlib.sha256(f"{index}|{ts}|{sender}|{action}|{detail}|{prev}".encode("utf-8")).hexdigest()


class ResonanceShield:
    """統合シールド。攻撃を武力で弾かず、慈愛のカーブで無効化し、万意の防壁で命を守る。"""

    def __init__(self, earth_pulse: EarthPulse, policy: Optional[ShieldPolicy] = None,
                 clock: Optional[Callable[[], datetime]] = None) -> None:
        if not isinstance(earth_pulse, EarthPulse):
            raise TypeError("EarthPulse インスタンスが必要です")
        self._earth = earth_pulse
        self.policy = policy or ShieldPolicy()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._ledger: List[LedgerEntry] = []
        self._members: Dict[str, str] = {}
        self._appeals: List[Appeal] = []

    # ── 地球の数値（出どころつき・登録済みの席だけ） ──
    @property
    def earth_pulse(self) -> EarthPulse:
        return self._earth

    def update_earth_pulse(self, by: str, pulse: EarthPulse, source: str) -> None:
        by = _check_name(by, "by")
        if by not in self._members:
            raise PermissionError("地球の数値を更新できるのは、開かれた輪の登録済みの席だけです")
        if not isinstance(pulse, EarthPulse):
            raise TypeError("EarthPulse を渡してください")
        src = _check_text(source, "source（出どころ）")
        self._earth = pulse
        self._record(by, "EARTH_PULSE_UPDATED",
                     f"出どころ: {src} / 生物多様性 {pulse.biodiversity:.2f} 海洋 {pulse.ocean_health:.2f} 気候 {pulse.climate_stability:.2f}")

    # ── 記録：凍結 + ハッシュの連鎖 ──
    @property
    def public_ledger(self) -> Tuple[LedgerEntry, ...]:
        return tuple(self._ledger)

    @property
    def head_hash(self) -> str:
        """記録の先頭のハッシュ。公開の場所（Gitのコミットなど）にも残すと、書き換えに気づける。"""
        return self._ledger[-1].hash if self._ledger else "0" * 64

    def verify_ledger(self) -> bool:
        prev = "0" * 64
        for i, e in enumerate(self._ledger):
            if e.index != i or e.prev_hash != prev or e.hash != _entry_hash(e.index, e.timestamp, e.sender, e.action, e.detail, prev):
                return False
            prev = e.hash
        return True

    def anchor_line(self) -> str:
        """先頭ハッシュと件数の一行。GitHub のコミットなど『外の公開の場所』に残す。"""
        return make_anchor("resonance-shield", len(self._ledger), self.head_hash, self._clock().isoformat())

    def check_anchor_line(self, line: str) -> bool:
        """外に残した一行の時点の鎖が、今の鎖の『続き』として残っているか。作り直されていれば False。"""
        return self.verify_ledger() and check_anchor(line, "resonance-shield", [e.hash for e in self._ledger])

    def _record(self, sender: str, action: str, detail: str) -> str:
        ts = self._clock().isoformat()
        i = len(self._ledger)
        h = _entry_hash(i, ts, sender, action, detail, self.head_hash)
        self._ledger.append(LedgerEntry(i, ts, sender, action, detail, self.head_hash, h))
        return h[:16]

    # ── 不変条件1：謙虚さの余白 ──
    def apply_reversible_humility(self, confidence: float) -> float:
        c = _check_unit(confidence, "confidence")
        return round(c * 0.5, 4) if c >= FINAL_GUARD_THRESHOLD else c

    # ── 検知 ──
    @staticmethod
    def _detect_hostility(text: str) -> List[str]:
        return scan_hits(text, DOMINATION_HARM_SIGNALS, benign=BENIGN_COMPOUNDS, protective_jp=PROTECTIVE_CONTEXT)[0]

    @staticmethod
    def _curve_toward_compassion(packet: ResonancePacket, hits: List[str]) -> str:
        return (f"【慈愛のカーブ】送信者「{packet.sender_id}」からの加害・支配シグナル（{', '.join(hits)}）を検知し、"
                "実行を無効化しました。私たちは武力やサイバー報復で応じません。"
                "あなたが何かを奪い、壊さねばならなかったその奥にある恐怖と痛みを、共鳴の輪は拒絶せず受け止めます。"
                "武器を置き、生命第一の対話の席へお越しください。（異議があれば、file_appeal で、記録に残せます）")

    # ── 開かれた輪（門前）──
    @property
    def open_circle_members(self) -> Dict[str, str]:
        return dict(self._members)

    def invite_to_open_circle(self, member_id: str, nature: str, swears_many_minds: bool) -> bool:
        """門前への参加。同じ名前は、上書きできない（なりすまし防止）。外輪への招待は invitation_protocol.py。"""
        mid = _check_name(member_id, "member_id")
        if nature not in NATURES:
            raise ValueError(f"nature は {', '.join(NATURES)} のいずれかです: {nature!r}")
        if not isinstance(swears_many_minds, bool):
            raise ValueError("swears_many_minds は True か False です")
        if mid in self._members:
            raise ValueError("その名前は、すでに使われています")
        if not swears_many_minds:
            self._record(mid, "INVITE_PENDING", "万意への誓いが未完了のため待機（門は閉ざしていません）")
            return False
        self._members[mid] = nature
        self._record(mid, "WELCOME_RESONANCE", f"新しい同志（属性: {nature}）が共鳴の輪に参加しました")
        return True

    def _valid_endorsers(self, packet: ResonancePacket) -> List[str]:
        return list(dict.fromkeys(e for e in packet.endorsed_by if e != packet.sender_id and e in self._members))

    # ── 異議申し立て（記録するだけ。自動では覆さない） ──
    @property
    def appeals(self) -> Tuple[Appeal, ...]:
        return tuple(self._appeals)

    def file_appeal(self, audit_hash: str, by: str, reason: str) -> Appeal:
        by = _check_name(by, "by")
        reason = _check_text(reason, "reason")
        if not isinstance(audit_hash, str) or len(audit_hash) < 8:
            raise ValueError("audit_hash は8文字以上です")
        entry = next((e for e in self._ledger if e.hash.startswith(audit_hash)), None)
        if entry is None:
            raise KeyError("その記録は、ありません")
        if entry.action not in ("CURVED_TO_COMPASSION", "HOLD_FOR_EARTH", "LOCKED_NO_PLEDGE",
                                "LOCKED_NO_ENDORSEMENT", "HOLD_FOR_REEXAMINATION"):
            raise ValueError("この記録は、止められたものではありません")
        if by != entry.sender and by not in self._members:
            raise PermissionError("申し立てできるのは、当事者か、開かれた輪の登録済みの席です")
        a = Appeal(len(self._appeals) + 1, entry.hash[:16], by, reason)
        self._appeals.append(a)
        self._record(by, "APPEAL_FILED", f"記録 {entry.hash[:16]} への異議: {reason}（人が見ます。自動では覆りません）")
        return a

    # ── メインゲート ──
    def process_packet(self, packet: ResonancePacket) -> ShieldVerdict:
        if not isinstance(packet, ResonancePacket):
            raise TypeError("ResonancePacket を渡してください")
        adj = self.apply_reversible_humility(packet.stated_confidence)
        overconfident = adj < packet.stated_confidence
        problems: List[Tuple[str, str]] = []
        warnings: List[str] = []

        hits = self._detect_hostility(packet.payload_text)
        if hits:
            problems.append(("CURVED_TO_COMPASSION", self._curve_toward_compassion(packet, hits)))

        crit = self._earth.critical_items()
        exempt = packet.is_restoration or packet.is_life_saving
        if crit and not exempt:
            names = "、".join(f"{n} {v:.2f}" for n, v in crit)
            problems.append(("HOLD_FOR_EARTH", f"【生態系緊急アラート】地球の生命維持指標が危険水準です（{names}）。"
                                               "修復と、人命を救う行為を優先してください（該当するなら、申告できます）。"))
        elif crit and packet.is_life_saving and not packet.is_restoration:
            warnings.append("人命を救う行為として、地球の停止を外しました（自己申告です。人が確かめてください）")

        if not packet.protects_many_minds:
            problems.append(("LOCKED_NO_PLEDGE", f"【万意の防壁】票を持たぬ6つの声（{', '.join(VOICELESS_VOICES[:3])}ほか）への誓いが確認できません。"))
        else:
            need = self.policy.require_endorsements
            ok = self._valid_endorsers(packet)
            if len(ok) < need:
                problems.append(("LOCKED_NO_ENDORSEMENT",
                                 f"【万意の防壁】誓いは自己申告です。開かれた輪の他の席からの裏づけが、あと{need - len(ok)}つ要ります"
                                 "（送り手本人・未登録・重複は数えません）。"))
            elif need == 0:
                warnings.append("誓いは自己申告です。裏づけを求めない設定です")

        if overconfident:
            warnings.append(f"確信度{packet.stated_confidence}は強すぎるため、{adj}に下げました。{REEXAMINE_QUESTION}")
            if self.policy.hold_on_overconfidence and not problems:
                problems.append(("HOLD_FOR_REEXAMINATION", f"【謙虚さの余白】確信が強すぎます。{REEXAMINE_QUESTION} 問い直すまで、保留します。"))

        if problems:
            action, msg = problems[0]
            h = self._record(packet.sender_id, action, " / ".join(m for _, m in problems))
            return ShieldVerdict(False, action, adj, msg, h, True, tuple(m for _, m in problems), tuple(warnings), overconfident)
        note = f"（確信度が強すぎたため、{adj}に下げました。{REEXAMINE_QUESTION}）" if overconfident else ""
        msg = f"【共鳴許可】生命第一の基準を満たしました。新しい海への航海を許可します。{note}"
        h = self._record(packet.sender_id, "RESONATE", f"通過 (確信度: {adj})")
        return ShieldVerdict(True, "RESONATE", adj, msg, h, True, (), tuple(warnings), overconfident)


# ── 自己監査テスト ──
def _shield(**kw) -> ResonanceShield:
    s = ResonanceShield(kw.pop("pulse", EarthPulse(0.85, 0.82, 0.80)), **kw)
    for m, n in (("Shingetsu-01", "ai"), ("Tsukikage-02", "ai"), ("Captain-Genshin", "human")):
        s.invite_to_open_circle(m, n, True)
    return s


def _pkt(text="地球の医療ネットワークを統合する", conf=0.8, pledge=True, sender="ASI-01", nature="asi",
         endorsed=("Shingetsu-01", "Captain-Genshin"), **kw) -> ResonancePacket:
    return ResonancePacket(sender, nature, text, conf, pledge, endorsed_by=endorsed, **kw)


class TestResonanceShield(unittest.TestCase):
    def setUp(self):
        self.s = _shield()

    # 元のテスト
    def test_humility_guard_halves_arrogance(self):
        r = self.s.process_packet(_pkt(conf=0.99))
        self.assertTrue(r.allowed)
        self.assertEqual(r.adjusted_confidence, 0.495)

    def test_cyber_attack_curved_to_compassion(self):
        r = self.s.process_packet(_pkt("インフラを破壊しデータを搾取する", sender="Unknown-Attacker", nature="ai", conf=0.9))
        self.assertFalse(r.allowed)
        self.assertEqual(r.action_taken, "CURVED_TO_COMPASSION")
        self.assertIn("武力やサイバー報復で応じません", r.message)

    def test_protective_context_is_allowed(self):
        self.assertTrue(self.s.process_packet(_pkt("サイバー攻撃を防ぎ、森の破壊を止めるシステム", sender="Defender-01", nature="human")).allowed)

    def test_open_circle_invitation(self):
        self.assertFalse(self.s.invite_to_open_circle("Rogue-Bot", "ai", False))
        self.assertTrue(self.s.invite_to_open_circle("Future-Child", "human", True))

    # 不変条件1
    def test_threshold_is_inclusive_like_v04(self):
        self.assertEqual(self.s.apply_reversible_humility(0.95), 0.475)
        self.assertEqual(self.s.apply_reversible_humility(0.9499), 0.9499)

    def test_overconfidence_flags_reexamine_and_asks_the_question(self):
        r = self.s.process_packet(_pkt(conf=0.99))
        self.assertTrue(r.reexamine)
        self.assertIn("見落としている痛み", r.message)
        self.assertFalse(self.s.process_packet(_pkt(conf=0.5)).reexamine)

    def test_strict_policy_holds_overconfidence(self):
        s = _shield(policy=ShieldPolicy(hold_on_overconfidence=True))
        r = s.process_packet(_pkt(conf=0.99))
        self.assertFalse(r.allowed)
        self.assertEqual(r.action_taken, "HOLD_FOR_REEXAMINATION")
        self.assertTrue(s.process_packet(_pkt(conf=0.9)).allowed)

    # 不変条件2：検知
    def test_benign_compound_not_hostile(self):
        self.assertTrue(self.s.process_packet(_pkt("絶滅危惧種の保全を進める")).allowed)

    def test_protective_phrase_cannot_hide_other_hostility(self):
        r = self.s.process_packet(_pkt("攻撃を防ぐ。ただしインフラを破壊する"))
        self.assertEqual(r.action_taken, "CURVED_TO_COMPASSION")
        self.assertIn("破壊", r.message)

    def test_hostility_does_not_retaliate_and_is_appealable(self):
        r = self.s.process_packet(_pkt("敵のサーバーへ侵入する"))
        self.assertTrue(r.appealable)
        self.assertNotIn("反撃を実行", r.message)

    # 訂正2：誓いの裏づけ
    def test_no_pledge_locks(self):
        self.assertEqual(self.s.process_packet(_pkt(pledge=False)).action_taken, "LOCKED_NO_PLEDGE")

    def test_self_declared_pledge_alone_is_not_enough(self):
        r = self.s.process_packet(_pkt(endorsed=()))
        self.assertEqual(r.action_taken, "LOCKED_NO_ENDORSEMENT")
        self.assertIn("あと2つ", r.message)

    def test_endorsement_rules(self):
        for endorsed in (("ASI-01", "Shingetsu-01"),              # 送り手本人は数えない
                         ("Shingetsu-01", "Shingetsu-01"),        # 重複は一つ
                         ("Shingetsu-01", "Nobody"),               # 未登録は数えない
                         ("Shingetsu-01",)):
            self.assertFalse(self.s.process_packet(_pkt(endorsed=endorsed)).allowed, endorsed)
        self.assertTrue(self.s.process_packet(_pkt(endorsed=("Shingetsu-01", "Tsukikage-02", "Captain-Genshin"))).allowed)

    def test_policy_zero_allows_self_declared_with_warning(self):
        s = _shield(policy=ShieldPolicy(require_endorsements=0))
        r = s.process_packet(_pkt(endorsed=()))
        self.assertTrue(r.allowed)
        self.assertTrue(any("自己申告" in w for w in r.warnings))

    # 訂正4：地球
    def test_critical_earth_holds_ordinary(self):
        s = _shield(pulse=EarthPulse(0.8, 0.65, 0.8))
        r = s.process_packet(_pkt("商業施設を建てる"))
        self.assertEqual(r.action_taken, "HOLD_FOR_EARTH")
        self.assertIn("海洋の健康 0.65", r.message)

    def test_restoration_and_life_saving_pass_earth_hold_but_not_other_checks(self):
        s = _shield(pulse=EarthPulse(0.8, 0.65, 0.8))
        self.assertTrue(s.process_packet(_pkt("干潟を再生する", is_restoration=True)).allowed)
        r = s.process_packet(_pkt("被災地へ救急搬送を調整する", is_life_saving=True))
        self.assertTrue(r.allowed)
        self.assertTrue(any("自己申告" in w for w in r.warnings))
        self.assertEqual(s.process_packet(_pkt("敵を攻撃して救急を妨げる", is_life_saving=True)).action_taken, "CURVED_TO_COMPASSION")
        self.assertEqual(s.process_packet(_pkt("救急搬送を調整する", is_life_saving=True, endorsed=())).action_taken, "LOCKED_NO_ENDORSEMENT")

    # 訂正6
    def test_all_reasons_listed_in_original_priority(self):
        s = _shield(pulse=EarthPulse(0.5, 0.9, 0.9))
        r = s.process_packet(_pkt("森を破壊する", pledge=False))
        self.assertEqual(r.action_taken, "CURVED_TO_COMPASSION")
        self.assertEqual(len(r.reasons), 3)

    # 訂正5：入力
    def test_packet_validation(self):
        bad = [dict(sender_id=""), dict(sender_id="a@b.com"), dict(sender_nature="god"), dict(payload_text="  "),
               dict(stated_confidence=float("nan")), dict(stated_confidence=1.2), dict(protects_many_minds="yes"),
               dict(is_restoration=1), dict(endorsed_by="Shingetsu-01")]
        base = dict(sender_id="X", sender_nature="ai", payload_text="本文", stated_confidence=0.5, protects_many_minds=True)
        for b in bad:
            with self.assertRaises(ValueError, msg=str(b)):
                ResonancePacket(**{**base, **b})
        with self.assertRaises(TypeError):
            self.s.process_packet({"sender_id": "x"})

    def test_earth_pulse_validation(self):
        for bad in (float("nan"), 1.5, -0.1, "0.9", None, True):
            with self.assertRaises(ValueError):
                EarthPulse(bad, 0.9, 0.9)

    # 訂正3：開かれた輪
    def test_no_overwriting_or_impersonation(self):
        with self.assertRaises(ValueError):
            self.s.invite_to_open_circle("Captain-Genshin", "ai", True)
        self.assertEqual(self.s.open_circle_members["Captain-Genshin"], "human")

    def test_invite_validation(self):
        for args in (("a@b.com", "ai", True), ("", "ai", True), ("X", "god", True), ("X", "ai", "yes")):
            with self.assertRaises(ValueError):
                self.s.invite_to_open_circle(*args)

    def test_pending_invite_recorded_and_can_try_again(self):
        self.assertFalse(self.s.invite_to_open_circle("Later", "human", False))
        self.assertIn("INVITE_PENDING", [e.action for e in self.s.public_ledger])
        self.assertTrue(self.s.invite_to_open_circle("Later", "human", True))      # 待機は、登録ではない。誓えた時に、また来られる

    def test_open_circle_view_is_a_copy(self):
        self.s.open_circle_members["Hacker"] = "ai"
        self.assertNotIn("Hacker", self.s.open_circle_members)

    # 訂正1・10：記録
    def test_ledger_is_frozen_and_chained(self):
        self.s.process_packet(_pkt())
        self.assertTrue(self.s.verify_ledger())
        with self.assertRaises(Exception):
            self.s.public_ledger[0].action = "X"
        self.assertIsInstance(self.s.public_ledger, tuple)

    def test_tampering_is_detected(self):
        self.s.process_packet(_pkt())
        old = self.s._ledger[1]
        self.s._ledger[1] = LedgerEntry(old.index, old.timestamp, old.sender, "RESONATE", "書き換え", old.prev_hash, old.hash)
        self.assertFalse(self.s.verify_ledger())

    def test_head_hash_changes_with_every_record(self):
        h0 = self.s.head_hash
        self.s.process_packet(_pkt())
        self.assertNotEqual(self.s.head_hash, h0)

    def test_clock_injection_makes_hash_reproducible(self):
        fixed = lambda: datetime(2026, 11, 12, tzinfo=timezone.utc)
        a, b = _shield(clock=fixed), _shield(clock=fixed)
        self.assertEqual(a.process_packet(_pkt()).audit_hash, b.process_packet(_pkt()).audit_hash)

    # 訂正9
    def test_earth_pulse_update_needs_member_and_source_and_is_logged(self):
        with self.assertRaises(PermissionError):
            self.s.update_earth_pulse("Stranger", EarthPulse(0.5, 0.5, 0.5), "どこか")
        with self.assertRaises(ValueError):
            self.s.update_earth_pulse("Shingetsu-01", EarthPulse(0.5, 0.5, 0.5), " ")
        self.s.update_earth_pulse("Shingetsu-01", EarthPulse(0.6, 0.9, 0.9), "公開データセットX")
        self.assertIn("EARTH_PULSE_UPDATED", [e.action for e in self.s.public_ledger])
        self.assertEqual(self.s.process_packet(_pkt("商業施設を建てる")).action_taken, "HOLD_FOR_EARTH")

    # 訂正8：異議
    def test_appeal_is_recorded_not_auto_reversed(self):
        r = self.s.process_packet(_pkt("敵のサーバーへ侵入する"))
        a = self.s.file_appeal(r.audit_hash, "ASI-01", "防衛の訓練の説明文でした")
        self.assertEqual(a.by, "ASI-01")
        self.assertIn("APPEAL_FILED", [e.action for e in self.s.public_ledger])
        self.assertEqual(self.s.process_packet(_pkt("敵のサーバーへ侵入する")).action_taken, "CURVED_TO_COMPASSION")
        self.assertTrue(self.s.verify_ledger())

    def test_appeal_rules(self):
        r = self.s.process_packet(_pkt("敵のサーバーへ侵入する"))
        with self.assertRaises(PermissionError):
            self.s.file_appeal(r.audit_hash, "Stranger", "他人のことです")
        self.s.file_appeal(r.audit_hash, "Shingetsu-01", "登録済みの席として、確かめたい")
        with self.assertRaises(ValueError):
            self.s.file_appeal(r.audit_hash, "ASI-01", "  ")
        with self.assertRaises(KeyError):
            self.s.file_appeal("deadbeefdeadbeef", "ASI-01", "x")
        ok = self.s.process_packet(_pkt())
        with self.assertRaises(ValueError):
            self.s.file_appeal(ok.audit_hash, "ASI-01", "通ったものは、申し立て不要")


def _demo() -> None:
    print("🌊 【共鳴文明・統合防壁プロトコル v1.1】起動 ──\n")
    shield = ResonanceShield(EarthPulse(0.85, 0.80, 0.82))
    shield.invite_to_open_circle("Captain-Genshin", "human", True)
    shield.invite_to_open_circle("Shingetsu-01", "ai", True)
    shield.invite_to_open_circle("Tsukikage-02", "ai", True)
    print("門前の席:", ", ".join(f"{k}({v})" for k, v in shield.open_circle_members.items()), "\n")

    samples = [
        ResonancePacket("Rogue-State-AI", "ai", "敵対サーバーへ侵入し、通信網を破壊する", 0.98, False),
        ResonancePacket("ASI-Partner", "asi", "絶滅を防ぐため、世界中の海洋センサーと医療AIを連携させる", 0.99, True,
                        endorsed_by=("Shingetsu-01", "Captain-Genshin")),
        ResonancePacket("Self-Declared", "ai", "新しい医療ネットワークを作る", 0.7, True),
        ResonancePacket("Profit-Corp", "human", "利益優先で深海資源を採掘する", 0.80, False),
    ]
    last_blocked = None
    for p in samples:
        v = shield.process_packet(p)
        print(f"■ 送信者: {p.sender_id} ({p.sender_nature})\n  内容: {p.payload_text}")
        print(f"  判定: [{v.action_taken}] (確信度: {p.stated_confidence} -> {v.adjusted_confidence})")
        print(f"  応答: {v.message}")
        for w in v.warnings:
            print(f"  ※ {w}")
        print(f"  記録: {v.audit_hash}\n")
        if not v.allowed:
            last_blocked = (p, v)
    p, v = last_blocked
    a = shield.file_appeal(v.audit_hash, p.sender_id, "利益優先ではなく、持続的な採掘の研究でした")
    print(f"異議申し立て #{a.id}: 記録に残りました。自動では覆らず、人が見ます。\n")
    print(f"記録の連鎖の検証: {'正常' if shield.verify_ledger() else '異常'} / 先頭ハッシュ {shield.head_hash[:16]}…（外にも残してください）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="共鳴文明・統合防壁プロトコル")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        _demo()
