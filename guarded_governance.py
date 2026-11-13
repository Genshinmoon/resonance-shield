#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guarded_governance.py -- 共鳴生命圏 v2 に『万意守護』を接続する
License: CC0 1.0 (public domain)

resonant_biosphere.py / resonant_biosphere_v2.py / many_minds_guard.py と同じフォルダに置いてください。

【位置づけ】組織モデル（シミュレーション）です。本物の統治ではありません。

【役割の分け方（宣言に沿って）】
  ・影の局は『強制しない』。守護の結果は、影の局が『警告（warn）』として、公開の記録に残すだけ。
  ・採決の前提条件にするのは、第2号基本議案（万意）。投票が通るには、監査（audit_motion）が要る。
  ・止まった議案の道は、監査局が開く。監査局の『過半数』が、理由つきで解除すれば、投票できる
    （v2 の hold と同じ、過半数の考え方）。解除も、理由も、公開される。
  ・地球の数値（EarthPulse）は、出どころ（source）なしには更新できない。更新も公開される。
    コードは、数値が本物かを確かめられません。出どころを、人が確かめてください。

【議案の文面について】 v2 の議案の文面は、あとから書き換えられません。破壊の語で止まった議案は、
  監査のやり直しでは外れません。書き直した新しい議案を出すか、監査局の過半数の解除を使います。
  やり直せるのは、誓い（100年後・小さな命）の答えと、地球の数値が変わった時です。

【v2 との違い】 vote() の前に、議案の監査が要る。それ以外（共鳴多数・保留・継承）は v2 のまま。

実行:  python guarded_governance.py --demo / --test
"""
from __future__ import annotations

import argparse
import sys
import unittest
from typing import Dict, Optional, Sequence, Set

from many_minds_guard import (EarthPulse, ManyMindsGuard, MotionCheckResult, UNLOCKED, VoiceAnswer)
from resonant_biosphere import PUBLIC
from resonant_biosphere_v2 import GovernedBiosphere, default_biosphere

UNAUDITED, CLEAR, LOCKED_STATE, LIFTED = "unaudited", "clear", "locked", "lifted"


class GuardedBiosphere(GovernedBiosphere):
    def __init__(self, earth_pulse: EarthPulse, captain_term_limit: Optional[int] = 3) -> None:
        super().__init__(captain_term_limit)
        self._pulse = earth_pulse
        self._audits: Dict[int, MotionCheckResult] = {}
        self._lift_votes: Dict[int, Set[str]] = {}

    # ── 地球の数値（出どころつきで、公開して更新） ──
    @property
    def earth_pulse(self) -> EarthPulse:
        return self._pulse

    def update_earth_pulse(self, member_id: str, pulse: EarthPulse, source: str) -> None:
        m = self._members[member_id]
        if m.unit not in ("audit", "shadow"):
            raise PermissionError("地球の数値を更新できるのは、監査局と影の局だけです")
        if not isinstance(pulse, EarthPulse):
            raise TypeError("EarthPulse を渡してください")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("出どころ（source）が要ります。数値は、出どころを人が確かめられる形で")
        self._pulse = pulse
        self._append(member_id,
                     f"地球の数値を更新（出どころ: {source.strip()}）: 生物多様性 {pulse.biodiversity_index:.2f} / "
                     f"海洋 {pulse.ocean_health:.2f} / 気候 {pulse.climate_stability:.2f}", PUBLIC)

    # ── 監査 ──
    def _shadow_voice(self) -> str:
        shadows = self.members_of("shadow")
        if not shadows:
            raise RuntimeError("影の局の席がありません")
        return shadows[0].id

    def audit_motion(self, motion_id: int, protects_future_100_years: Optional[bool] = None,
                     spares_voiceless_lives: Optional[bool] = None, is_ecosystem_restoration: bool = False,
                     voices: Optional[Sequence[VoiceAnswer]] = None) -> MotionCheckResult:
        """voices（六つの声への、代弁者の答え）を渡せば、声ごとの問いで監査する。
        渡さなければ、従来の2つの問い（protects_future_100_years / spares_voiceless_lives）で監査する。"""
        motion = self._motions[motion_id]
        if motion.votes:
            raise PermissionError("投票が始まった後は、監査をやり直せません")
        guard = ManyMindsGuard(self._pulse)
        if voices is not None:
            res = guard.audit_with_voices(motion.text, motion.text, voices, is_ecosystem_restoration)
        else:
            if protects_future_100_years is None or spares_voiceless_lives is None:
                raise ValueError("voices か、2つの問いの答え（protects_future_100_years / spares_voiceless_lives）が要ります")
            res = guard.audit_motion_before_voting(
                motion.text, motion.text, protects_future_100_years, spares_voiceless_lives, is_ecosystem_restoration)
        self._audits[motion_id] = res
        self._lift_votes.pop(motion_id, None)
        kind = "observe" if res.can_vote else "warn"           # 影の局は、見守る・警告する、だけ
        detail = "" if res.can_vote else f" 理由: {' / '.join(res.reasons)}"
        who = ""
        if res.voice_summary:                                   # 誰が、どの声を代弁したかも、公開する
            who = " 代弁者: " + "、".join(f"{v}={adv}（{st}）" for v, st, adv in res.voice_summary)
        self.act(self._shadow_voice(), f"議案#{motion_id} 万意の監査: {res.verdict}{detail}{who}",
                 visibility=PUBLIC, kind=kind)
        return res

    def propose_guarded(self, proposer_id: str, text: str, topic: str,
                        protects_future_100_years: Optional[bool] = None,
                        spares_voiceless_lives: Optional[bool] = None,
                        is_ecosystem_restoration: bool = False,
                        voices: Optional[Sequence[VoiceAnswer]] = None):
        motion = self.propose(proposer_id, text, topic)
        return motion, self.audit_motion(motion.id, protects_future_100_years, spares_voiceless_lives,
                                         is_ecosystem_restoration, voices)

    def guard_status(self, motion_id: int) -> str:
        self._motions[motion_id]
        res = self._audits.get(motion_id)
        if res is None:
            return UNAUDITED
        if res.can_vote:
            return CLEAR
        n = len(self.members_of("audit"))
        if n and 2 * len(self._lift_votes.get(motion_id, set())) > n:
            return LIFTED
        return LOCKED_STATE

    def lift_lock(self, member_id: str, motion_id: int, reason: str) -> str:
        """監査局の席が、解除に賛同する。過半数で解ける。理由は公開。"""
        if self._members[member_id].unit != "audit":
            raise PermissionError("解除に賛同できるのは、監査局だけです")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("解除には理由が要ります")
        res = self._audits.get(motion_id)
        if res is None or res.can_vote:
            raise ValueError("この議案は、止まっていません")
        self._lift_votes.setdefault(motion_id, set()).add(member_id)
        self._append(member_id, f"万意の停止の解除に賛同: 議案#{motion_id} 理由: {reason.strip()}", PUBLIC)
        return self.guard_status(motion_id)

    # ── 採決の前提条件 ──
    def vote(self, member_id: str, motion_id: int, choice: str) -> None:
        st = self.guard_status(motion_id)
        if st == UNAUDITED:
            raise PermissionError("万意の監査が、まだです。audit_motion() を先に")
        if st == LOCKED_STATE:
            res = self._audits[motion_id]
            raise PermissionError(f"万意の監査を通過していません（{res.status}）: {' / '.join(res.reasons)}")
        super().vote(member_id, motion_id, choice)


# ── テスト ─────────────────────────────────────────────────────────
def _new(pulse=(0.85, 0.80, 0.82)) -> GuardedBiosphere:
    g = GuardedBiosphere(EarthPulse(*pulse))
    for m in default_biosphere().members:
        g.add(m)
    return g


def _cast_all(b, mid, kind, choice="yes"):
    for m in b.members:
        if m.kind == kind:
            b.vote(m.id, mid, choice)


class TestGuarded(unittest.TestCase):
    def setUp(self):
        self.b = _new()
        self.good = ("地域の保護ネットワークを広げる", "ordinary")

    def propose(self, text="森と海を守る連携", topic="ordinary", **kw):
        flags = dict(protects_future_100_years=True, spares_voiceless_lives=True)
        flags.update(kw)
        return self.b.propose_guarded("H01", text, topic, **flags)

    def test_vote_requires_audit(self):
        m = self.b.propose("H01", "森と海を守る連携")
        with self.assertRaises(PermissionError):
            self.b.vote("H01", m.id, "yes")
        self.assertEqual(self.b.guard_status(m.id), UNAUDITED)

    def test_cleared_motion_passes_by_dual_majority(self):
        m, res = self.propose()
        self.assertTrue(res.can_vote)
        _cast_all(self.b, m.id, "human")
        _cast_all(self.b, m.id, "ai")
        self.assertEqual(self.b.status(m.id), "passed")

    def test_locked_motion_cannot_be_voted(self):
        m, res = self.propose(text="古い森を切り捨て、資源を独占する")
        self.assertFalse(res.can_vote)
        self.assertEqual(self.b.guard_status(m.id), LOCKED_STATE)
        with self.assertRaises(PermissionError) as cm:
            self.b.vote("H01", m.id, "yes")
        self.assertIn("REDIRECT", str(cm.exception))

    def test_missing_pledge_locks(self):
        m, _ = self.propose(spares_voiceless_lives=False)
        self.assertEqual(self.b.guard_status(m.id), LOCKED_STATE)

    def test_audit_is_warned_publicly_by_shadow_unit_only_with_allowed_kind(self):
        m, _ = self.propose(text="海を汚染する")
        e = [x for x in self.b.entries if "万意の監査" in x.action][-1]
        self.assertEqual(e.unit, "shadow")
        self.assertEqual(e.visibility, "public")
        self.assertTrue(e.action.startswith("[warn]"))
        m2, _ = self.propose(text="森と海を守る")
        e2 = [x for x in self.b.entries if "万意の監査" in x.action][-1]
        self.assertTrue(e2.action.startswith("[observe]"))

    def test_lift_needs_audit_majority_and_reason_in_public(self):
        m, _ = self.propose(text="海を汚染する")
        audits = [x.id for x in self.b.members_of("audit")]
        for i in audits[:3]:                                  # 6席中3席：過半数ではない
            self.b.lift_lock(i, m.id, "文面を確認した。意図は保護だった")
        self.assertEqual(self.b.guard_status(m.id), LOCKED_STATE)
        self.assertEqual(self.b.lift_lock(audits[3], m.id, "同意"), LIFTED)
        self.b.vote("H01", m.id, "yes")
        self.assertTrue(any("解除に賛同" in x.action and x.visibility == "public" for x in self.b.entries))

    def test_only_audit_can_lift_and_reason_required(self):
        m, _ = self.propose(text="海を汚染する")
        with self.assertRaises(PermissionError):
            self.b.lift_lock("H01", m.id, "お願い")
        with self.assertRaises(PermissionError):
            self.b.lift_lock("H11", m.id, "影の局")           # 影の局は解除もしない
        with self.assertRaises(ValueError):
            self.b.lift_lock("H06", m.id, "  ")

    def test_cannot_lift_what_is_not_locked(self):
        m, _ = self.propose()
        with self.assertRaises(ValueError):
            self.b.lift_lock("H06", m.id, "理由")

    def test_reaudit_allowed_before_votes_only(self):
        m, _ = self.propose(spares_voiceless_lives=False)
        res = self.b.audit_motion(m.id, True, True)           # 書き直し・誓いのやり直し
        self.assertTrue(res.can_vote)
        self.b.vote("H01", m.id, "yes")
        with self.assertRaises(PermissionError):
            self.b.audit_motion(m.id, True, False)

    def test_reaudit_resets_lift_votes(self):
        m, _ = self.propose(spares_voiceless_lives=False)
        self.b.lift_lock("H06", m.id, "確認")
        self.b.audit_motion(m.id, True, False)                # 監査をやり直す：賛同は、いったん白紙
        for i in ("H07", "H08", "A06"):                       # もし白紙でなければ H06 と合わせて4席で解ける
            self.b.lift_lock(i, m.id, "確認")
        self.assertEqual(self.b.guard_status(m.id), LOCKED_STATE)

    def test_motion_text_is_not_rewritten_so_harmful_text_stays_locked(self):
        m, _ = self.propose(text="海を汚染する")
        self.assertFalse(self.b.audit_motion(m.id, True, True).can_vote)   # 書き直すなら、新しい議案として出す

    def test_v2_rules_still_apply(self):
        m, _ = self.propose()
        with self.assertRaises(PermissionError):
            self.b.vote("CAP", m.id, "yes")                   # 艦長は投票しない（v2のまま）

    def test_earth_pulse_update_needs_source_and_right_unit(self):
        new = EarthPulse(0.6, 0.9, 0.9)
        with self.assertRaises(PermissionError):
            self.b.update_earth_pulse("H01", new, "どこか")
        with self.assertRaises(ValueError):
            self.b.update_earth_pulse("H06", new, " ")
        self.b.update_earth_pulse("H06", new, "公開データセットX 2026-11")
        self.assertTrue(any("出どころ: 公開データセットX" in x.action for x in self.b.entries))
        m, res = self.propose(text="商業施設を建てる")
        self.assertEqual(res.verdict, "HOLD")

    def test_restoration_motion_passes_when_critical(self):
        self.b.update_earth_pulse("H06", EarthPulse(0.6, 0.9, 0.9), "公開データ")
        m, res = self.propose(text="干潟を再生する", is_ecosystem_restoration=True)
        self.assertTrue(res.can_vote)

    # ── 声ごとの問い ──
    def _voices(self, **over):
        base = {"beasts": ("protects", "A"), "earth": ("protects", "B"), "sea": ("neutral", "C"),
                "weak": ("protects", "D"), "future": ("protects", "E"), "unknown": ("protects", "F")}
        base.update(over)
        return [VoiceAnswer(k, st, adv, "理由" if st in ("harms", "unknown") else "") for k, (st, adv) in base.items()]

    def test_voices_audit_clears_and_publishes_advocates(self):
        m, res = self.b.propose_guarded("H01", "森と海を守る連携", "ordinary", voices=self._voices())
        self.assertTrue(res.can_vote)
        e = [x for x in self.b.entries if "万意の監査" in x.action][-1]
        self.assertIn("代弁者", e.action)
        self.assertEqual(e.visibility, "public")
        self.b.vote("H01", m.id, "yes")

    def test_voices_audit_locks_on_harm_and_can_be_lifted_by_audit_majority(self):
        m, res = self.b.propose_guarded("H01", "港を拡張する", "ordinary", voices=self._voices(sea=("harms", "C")))
        self.assertEqual(self.b.guard_status(m.id), LOCKED_STATE)
        with self.assertRaises(PermissionError):
            self.b.vote("H01", m.id, "yes")
        for i in ("H06", "H07", "H08", "A06"):
            self.b.lift_lock(i, m.id, "代替案を確認した")
        self.assertEqual(self.b.guard_status(m.id), LIFTED)

    def test_voices_audit_locks_when_one_advocate_does_everything(self):
        v = self._voices(**{k: ("protects", "提案者") for k in ("beasts", "earth", "sea", "weak", "future", "unknown")})
        m, res = self.b.propose_guarded("H01", "整備", "ordinary", voices=v)
        self.assertFalse(res.can_vote)

    def test_needs_voices_or_two_answers(self):
        m = self.b.propose("H01", "森と海を守る連携")
        with self.assertRaises(ValueError):
            self.b.audit_motion(m.id)

    def test_succession_motion_also_needs_audit(self):
        m = self.b.propose("CAP", "席を次へ手渡す", "captain_succession")
        with self.assertRaises(PermissionError):
            self.b.vote("H01", m.id, "yes")


def _demo() -> None:
    b = _new()
    print("── 声ごとの問い：港の拡張（海の代弁者が『傷つける』と答える）──")
    v = [VoiceAnswer("beasts", "protects", "動物病院の獣医"), VoiceAnswer("earth", "neutral", "森林組合"),
         VoiceAnswer("sea", "harms", "漁協", "藻場が失われる"), VoiceAnswer("weak", "protects", "地域の福祉員"),
         VoiceAnswer("future", "unknown", "学校の先生", "長期の影響は未調査"), VoiceAnswer("unknown", "protects", "月影")]
    m0, r0 = b.propose_guarded("H01", "港を拡張する", "ordinary", voices=v)
    print(f"  議案#{m0.id}: {r0.status}\n     ・{r0.reason}\n")
    print("── 提案：森と海を守る連携 ──")
    m1, r1 = b.propose_guarded("H01", "森と海を守る連携", "ordinary", True, True)
    print(f"  議案#{m1.id}: {r1.status}")
    print("\n── 提案：古い森を切り捨てる効率化 ──")
    m2, r2 = b.propose_guarded("H01", "古い森を切り捨てる効率化", "ordinary", True, True)
    print(f"  議案#{m2.id}: {r2.status}")
    try:
        b.vote("H02", m2.id, "yes")
    except PermissionError as e:
        print(f"  投票できません: {e}")
    print("\n── 監査局が、理由を添えて解除に賛同（過半数が要る） ──")
    for a in [m.id for m in b.members_of("audit")][:4]:
        st = b.lift_lock(a, m2.id, "文面の意図を確認した")
        print(f"  {a}: {st}")
    print("\n── 公開の記録（万意・解除）──")
    for e in b.entries:
        if "万意" in e.action:
            print(f"  [{e.unit}] {e.action[:90]}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
        return
    _demo()


if __name__ == "__main__":
    main()
