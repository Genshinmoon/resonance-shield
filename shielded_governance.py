#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shielded_governance.py -- 共鳴生命圏に『万意守護』と『統合防壁』を、ふたつながら接続する
License: CC0 1.0 (public domain)

同じフォルダに置くもの:
  resonant_biosphere.py / resonant_biosphere_v2.py / many_minds_guard.py /
  guarded_governance.py / resonance_shield_protocol.py / peace_shield.py

【位置づけ】組織モデル（シミュレーション）です。本物の統治・防衛ではありません。

【採決の前提条件（3つ）】
  1. 万意の監査（guarded_governance の audit_motion）
  2. 防壁の検査（shield_motion）: 加害の語・地球の危機・万意の誓い・確信度の謙虚さ
     + 不戦防壁（peace_shield.py）: 武力の語は凍結、恐れの語は保留。shield_motion が、自動で一緒に検査する。
     議案は『採るかどうかを決める提案』なので、不戦防壁は既定で厳しい側（directive）で見る。
  3. 誓いの裏づけ: 『他の席が、自分で』 endorse_pledge() する。送り手が名前を並べるのではない。
  どちらの停止も、監査局の『過半数』が、理由つきで解除できる。解除も理由も、公開される。

【防壁の単体版との違い】
  ・裏づけは、名前の申告ではなく、その席本人の公開の行為になる（なりすましで裏づけを増やせない）。
  ・防壁の記録の先頭ハッシュを、生命圏の公開の記録にも刻める（anchor_shield_ledger）。
    ふたつの記録が互いの証人になる。どちらかだけを書き換えれば、食い違いで気づける。
  ・異議（appeal）は、公開の記録にも残る。自動では覆らず、監査局が見る。

【限界】 キーワード検知は入口の見本です。裏づけは、席の行為の記録であって、心の中の確かめではありません。
  同じ顔ぶれが裏づけ合っていないかは、公開の記録（endorsements_of）を見て、人が確かめてください。

実行: python shielded_governance.py --demo / --test
"""
from __future__ import annotations

import argparse
import sys
import unittest
from typing import Dict, Optional, Sequence, Set, Tuple

import many_minds_guard as mmg
from guarded_governance import GuardedBiosphere, CLEAR, LIFTED, LOCKED_STATE, UNAUDITED
from resonance_shield_protocol import (EarthPulse as ShieldPulse, ResonancePacket, ResonanceShield,
                                       ShieldPolicy, ShieldVerdict)
from resonant_biosphere import AI, CAPTAIN, HUMAN, PUBLIC, UNKNOWN
from resonant_biosphere_v2 import default_biosphere
from peace_shield import DIRECTIVE, PeaceAndNonAggressionShield, PeaceVerdict

_NATURE = {HUMAN: "human", CAPTAIN: "human", AI: "ai", UNKNOWN: "wildcard"}


def _to_shield_pulse(p: mmg.EarthPulse) -> ShieldPulse:
    return ShieldPulse(p.biodiversity_index, p.ocean_health, p.climate_stability)


class ShieldedBiosphere(GuardedBiosphere):
    def __init__(self, earth_pulse: mmg.EarthPulse, captain_term_limit: Optional[int] = 3,
                 policy: Optional[ShieldPolicy] = None) -> None:
        super().__init__(earth_pulse, captain_term_limit)
        self._shield = ResonanceShield(_to_shield_pulse(earth_pulse), policy)
        self._peace = PeaceAndNonAggressionShield()
        self._peace_verdicts: Dict[int, PeaceVerdict] = {}
        self._verdicts: Dict[int, ShieldVerdict] = {}
        self._endorsers: Dict[int, Set[str]] = {}
        self._shield_lifts: Dict[int, Set[str]] = {}

    @property
    def shield(self) -> ResonanceShield:
        return self._shield

    @property
    def peace(self) -> PeaceAndNonAggressionShield:
        return self._peace

    def _blocked(self, motion_id: int) -> bool:
        v, pv = self._verdicts.get(motion_id), self._peace_verdicts.get(motion_id)
        return bool((v and not v.allowed) or (pv and not pv.action_allowed))

    def _sync(self) -> None:
        """生命圏の全席を、防壁の『開かれた輪』に写す（誓いは、席に就く時に済んでいるものとして）。"""
        have = self._shield.open_circle_members
        for m in self.members:
            if m.id not in have:
                self._shield.invite_to_open_circle(m.id, _NATURE[m.kind], True)

    # ── 地球の数値：両方に、出どころつきで ──
    def update_earth_pulse(self, member_id: str, pulse: mmg.EarthPulse, source: str) -> None:
        super().update_earth_pulse(member_id, pulse, source)
        self._sync()
        self._shield.update_earth_pulse(member_id, _to_shield_pulse(pulse), source.strip())

    # ── 誓いの裏づけ：その席本人の、公開の行為 ──
    def endorse_pledge(self, member_id: str, motion_id: int) -> int:
        m = self._members[member_id]
        motion = self._motions[motion_id]
        if m.kind == UNKNOWN:
            raise PermissionError("正体不明者は余白です。裏づけは出しません")
        if member_id == motion.proposer:
            raise PermissionError("提案者本人の裏づけは、数えません")
        if motion.votes:
            raise PermissionError("投票が始まった後は、裏づけを足せません")
        s = self._endorsers.setdefault(motion_id, set())
        if member_id in s:
            raise ValueError("すでに裏づけています")
        s.add(member_id)
        self._append(member_id, f"議案#{motion_id} の万意の誓いに、裏づけを添えました", PUBLIC)
        return len(s)

    def endorsements_of(self, motion_id: int) -> Tuple[str, ...]:
        self._motions[motion_id]
        return tuple(sorted(self._endorsers.get(motion_id, set())))

    # ── 防壁の検査 ──
    def shield_motion(self, motion_id: int, stated_confidence: float, protects_many_minds: bool,
                      is_restoration: bool = False, is_life_saving: bool = False,
                      peace_intent: str = DIRECTIVE) -> ShieldVerdict:
        motion = self._motions[motion_id]
        if motion.votes:
            raise PermissionError("投票が始まった後は、検査をやり直せません")
        self._sync()
        packet = ResonancePacket(motion.proposer, _NATURE[self._members[motion.proposer].kind], motion.text,
                                 stated_confidence, protects_many_minds, is_restoration, is_life_saving,
                                 tuple(sorted(self._endorsers.get(motion_id, set()))))
        v = self._shield.process_packet(packet)
        pv = self._peace.intercept_directive(motion.text, motion.proposer, peace_intent)
        self._verdicts[motion_id] = v
        self._peace_verdicts[motion_id] = pv
        self._shield_lifts.pop(motion_id, None)
        if pv.status != "HARMONY":                               # 不戦防壁の結果も、影の局が公開で知らせる
            self.act(self._shadow_voice(),
                     f"議案#{motion_id} 不戦防壁: {pv.status}（記録 {pv.audit_hash}） {pv.message}",
                     visibility=PUBLIC, kind="observe" if pv.action_allowed else "warn")
        kind = "observe" if v.allowed else "warn"
        detail = "" if v.allowed else f" 理由: {' / '.join(v.reasons)}"
        note = f" 注意: {' / '.join(v.warnings)}" if v.warnings else ""
        self.act(self._shadow_voice(), f"議案#{motion_id} 防壁の検査: {v.action_taken}（記録 {v.audit_hash}）{detail}{note}",
                 visibility=PUBLIC, kind=kind)
        return v

    def shield_status(self, motion_id: int) -> str:
        self._motions[motion_id]
        v = self._verdicts.get(motion_id)
        if v is None:
            return UNAUDITED
        if not self._blocked(motion_id):
            return CLEAR
        n = len(self.members_of("audit"))
        if n and 2 * len(self._shield_lifts.get(motion_id, set())) > n:
            return LIFTED
        return LOCKED_STATE

    def lift_shield(self, member_id: str, motion_id: int, reason: str) -> str:
        if self._members[member_id].unit != "audit":
            raise PermissionError("解除に賛同できるのは、監査局だけです")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("解除には理由が要ります")
        if motion_id not in self._verdicts or not self._blocked(motion_id):
            raise ValueError("この議案は、防壁で止まっていません")
        self._shield_lifts.setdefault(motion_id, set()).add(member_id)
        self._append(member_id, f"防壁の停止の解除に賛同: 議案#{motion_id} 理由: {reason.strip()}", PUBLIC)
        return self.shield_status(motion_id)

    def appeal(self, member_id: str, motion_id: int, reason: str):
        """止まった議案への異議。止めた防壁ごとに、記録に残る。自動では覆らず、監査局が見る。"""
        if motion_id not in self._verdicts or not self._blocked(motion_id):
            raise ValueError("この議案は、防壁で止まっていません")
        self._members[member_id]
        v, pv = self._verdicts[motion_id], self._peace_verdicts[motion_id]
        filed = []
        if not v.allowed:
            filed.append(self._shield.file_appeal(v.audit_hash, member_id, reason))
        if not pv.action_allowed:
            filed.append(self._peace.file_appeal(pv.audit_hash, member_id, reason))
        self._append(member_id, f"防壁の停止に異議: 議案#{motion_id} 理由: {reason.strip()}（監査局が見ます）", PUBLIC)
        return filed[0] if len(filed) == 1 else tuple(filed)

    def anchor_shield_ledger(self, member_id: str) -> str:
        """防壁の記録の先頭ハッシュを、生命圏の公開の記録に刻む。"""
        self._members[member_id]
        h = self._shield.head_hash
        self._append(member_id, f"防壁の記録の先頭ハッシュを刻印: {h[:16]}…（記録数 {len(self._shield.public_ledger)}）", PUBLIC)
        self._append(member_id, f"不戦防壁の記録の先頭ハッシュを刻印: {self._peace.head_hash[:16]}…（記録数 {len(self._peace.incident_log)}）", PUBLIC)
        return h

    def verify_anchors(self) -> bool:
        """ふたつの防壁の記録が壊れていないか。最後に刻んだ先頭ハッシュが、今の鎖の中に残っているかも見る。"""
        if not (self._shield.verify_ledger() and self._peace.verify_ledger()):
            return False
        acts = [e.action for e in self.entries]

        def last(prefix: str):
            marks = [x for x in acts if x.startswith(prefix)]
            if not marks:
                return None
            h = marks[-1].split("刻印: ")[1].split("…")[0]
            return None if set(h) == {"0"} else h          # まだ記録が無い時の刻印は、照合する相手が無い

        r, p = last("防壁の記録の先頭ハッシュを刻印: "), last("不戦防壁の記録の先頭ハッシュを刻印: ")
        return ((r is None or any(e.hash.startswith(r) for e in self._shield.public_ledger)) and
                (p is None or any(e.hash.startswith(p) for e in self._peace.incident_log)))

    # ── 採決の前提条件 ──
    def vote(self, member_id: str, motion_id: int, choice: str) -> None:
        st = self.shield_status(motion_id)
        if st == UNAUDITED:
            raise PermissionError("防壁の検査が、まだです。shield_motion() を先に")
        if st == LOCKED_STATE:
            v, pv = self._verdicts[motion_id], self._peace_verdicts[motion_id]
            why = list(v.reasons) if not v.allowed else []
            if not pv.action_allowed:
                why.append(f"不戦防壁 {pv.status}: {pv.message}")
            names = ([v.action_taken] if not v.allowed else []) + ([f"PEACE_{pv.status}"] if not pv.action_allowed else [])
            raise PermissionError(f"防壁を通過していません（{', '.join(names)}）: {' / '.join(why)}")
        super().vote(member_id, motion_id, choice)     # 万意の監査と、v2 の規則


# ── テスト ─────────────────────────────────────────────────────────
def _new(pulse=(0.85, 0.80, 0.82), **kw) -> ShieldedBiosphere:
    g = ShieldedBiosphere(mmg.EarthPulse(*pulse), **kw)
    for m in default_biosphere().members:
        g.add(m)
    return g


def _ids(b, kind, n):
    return [m.id for m in b.members if m.kind == kind][:n]


class TestShielded(unittest.TestCase):
    def setUp(self):
        self.b = _new()

    def passed(self, text="森と海を守る連携", conf=0.8, endorse=2, **kw):
        m = self.b.propose("H01", text, "ordinary")
        self.b.audit_motion(m.id, True, True)
        for e in _ids(self.b, HUMAN, 3)[1:1 + endorse]:
            self.b.endorse_pledge(e, m.id)
        return m, self.b.shield_motion(m.id, conf, True, **kw)

    def test_vote_needs_shield_check(self):
        m = self.b.propose("H01", "森と海を守る連携", "ordinary")
        self.b.audit_motion(m.id, True, True)
        with self.assertRaises(PermissionError):
            self.b.vote("H02", m.id, "yes")

    def test_cleared_by_both_and_voteable(self):
        m, v = self.passed()
        self.assertTrue(v.allowed)
        self.b.vote("H02", m.id, "yes")

    def test_guard_still_required(self):
        m = self.b.propose("H01", "森と海を守る連携", "ordinary")
        for e in _ids(self.b, HUMAN, 3)[1:3]:
            self.b.endorse_pledge(e, m.id)
        self.b.shield_motion(m.id, 0.8, True)
        with self.assertRaises(PermissionError):
            self.b.vote("H02", m.id, "yes")

    def test_not_enough_endorsements_locks(self):
        m, v = self.passed(endorse=1)
        self.assertEqual(v.action_taken, "LOCKED_NO_ENDORSEMENT")
        with self.assertRaises(PermissionError):
            self.b.vote("H02", m.id, "yes")

    def test_endorsement_rules(self):
        m = self.b.propose("H01", "森と海を守る連携", "ordinary")
        with self.assertRaises(PermissionError):
            self.b.endorse_pledge("H01", m.id)                       # 提案者本人
        unknown = [x.id for x in self.b.members if x.kind == UNKNOWN][0]
        with self.assertRaises(PermissionError):
            self.b.endorse_pledge(unknown, m.id)                     # 余白
        self.b.endorse_pledge("H02", m.id)
        with self.assertRaises(ValueError):
            self.b.endorse_pledge("H02", m.id)                       # 二重
        self.assertEqual(self.b.endorsements_of(m.id), ("H02",))
        self.assertIn("裏づけ", self.b.entries[-1].action)

    def test_cannot_forge_endorsement_by_name(self):
        m = self.b.propose("H01", "森と海を守る連携", "ordinary")
        self.b.audit_motion(m.id, True, True)
        v = self.b.shield_motion(m.id, 0.8, True)                    # 本人の行為が無ければ、0
        self.assertEqual(v.action_taken, "LOCKED_NO_ENDORSEMENT")

    def test_hostile_text_locked_and_shadow_only_warns(self):
        m, v = self.passed("敵のサーバーへ侵入する")
        self.assertEqual(v.action_taken, "CURVED_TO_COMPASSION")
        e = [x for x in self.b.entries if "防壁の検査" in x.action][-1]
        self.assertEqual(e.unit, "shadow")
        self.assertEqual(e.visibility, PUBLIC)

    def test_lift_needs_audit_majority_and_reason(self):
        m, v = self.passed("敵のサーバーへ侵入する")
        audits = [a.id for a in self.b.members_of("audit")]
        with self.assertRaises(PermissionError):
            self.b.lift_shield("H02", m.id, "理由")
        with self.assertRaises(ValueError):
            self.b.lift_shield(audits[0], m.id, " ")
        st = ""
        for a in audits[: len(audits) // 2 + 1]:
            st = self.b.lift_shield(a, m.id, "訓練文書の説明と確認した")
        self.assertEqual(st, LIFTED)
        self.b.vote("H02", m.id, "yes")

    def test_lift_only_when_blocked(self):
        m, v = self.passed()
        with self.assertRaises(ValueError):
            self.b.lift_shield(self.b.members_of("audit")[0].id, m.id, "理由")

    def test_reshield_allowed_before_votes_only(self):
        m, v = self.passed(endorse=1)
        self.b.endorse_pledge(_ids(self.b, HUMAN, 4)[3], m.id)
        self.assertTrue(self.b.shield_motion(m.id, 0.8, True).allowed)
        self.b.vote("H02", m.id, "yes")
        with self.assertRaises(PermissionError):
            self.b.shield_motion(m.id, 0.8, True)
        with self.assertRaises(PermissionError):
            self.b.endorse_pledge(_ids(self.b, HUMAN, 5)[4], m.id)

    def test_earth_critical_holds_ordinary_but_not_restoration(self):
        b = _new((0.85, 0.65, 0.82))
        m = b.propose("H01", "商業施設を建てる", "ordinary")
        for e in ("H02", "H03"):
            b.endorse_pledge(e, m.id)
        self.assertEqual(b.shield_motion(m.id, 0.8, True).action_taken, "HOLD_FOR_EARTH")
        m2 = b.propose("H01", "干潟を再生する", "ordinary")
        for e in ("H02", "H03"):
            b.endorse_pledge(e, m2.id)
        self.assertTrue(b.shield_motion(m2.id, 0.8, True, is_restoration=True).allowed)

    def test_earth_update_reaches_both_and_needs_source(self):
        a = self.b.members_of("audit")[0].id
        with self.assertRaises(ValueError):
            self.b.update_earth_pulse(a, mmg.EarthPulse(0.5, 0.9, 0.9), " ")
        self.b.update_earth_pulse(a, mmg.EarthPulse(0.5, 0.9, 0.9), "公開データX")
        self.assertAlmostEqual(self.b.shield.earth_pulse.biodiversity, 0.5)
        self.assertIn("EARTH_PULSE_UPDATED", [e.action for e in self.b.shield.public_ledger])

    def test_overconfidence_note_is_public(self):
        m, v = self.passed(conf=0.99)
        self.assertTrue(v.reexamine)
        self.assertTrue(any("見落としている痛み" in e.action for e in self.b.entries))

    def test_appeal_public_and_not_auto_reversed(self):
        m, v = self.passed("敵のサーバーへ侵入する")
        self.b.appeal("H02", m.id, "訓練の説明文でした")
        self.assertIn("異議", self.b.entries[-1].action)
        self.assertEqual(self.b.shield_status(m.id), LOCKED_STATE)
        ok, _ = self.passed()
        with self.assertRaises(ValueError):
            self.b.appeal("H02", ok.id, "通っている")

    def test_anchor_and_verify(self):
        self.passed()
        h = self.b.anchor_shield_ledger("H01")
        self.assertEqual(h, self.b.shield.head_hash)
        self.assertTrue(self.b.verify_anchors())
        self.passed()                                                 # 鎖は伸びても、刻印は残る
        self.assertTrue(self.b.verify_anchors())

    def test_tampering_detected_by_anchor(self):
        self.passed()
        self.b.anchor_shield_ledger("H01")
        led = self.b.shield._ledger
        from resonance_shield_protocol import LedgerEntry, _entry_hash
        # 鎖を、最初から作り直す（内部の者の手口）
        prev, new = "0" * 64, []
        for e in led:
            d = "書き換え" if e.index == 1 else e.detail
            h = _entry_hash(e.index, e.timestamp, e.sender, e.action, d, prev)
            new.append(LedgerEntry(e.index, e.timestamp, e.sender, e.action, d, prev, h))
            prev = h
        self.b.shield._ledger[:] = new
        self.assertTrue(self.b.shield.verify_ledger())                # 鎖だけ見れば、正しく見える
        self.assertFalse(self.b.verify_anchors())                     # 公開の刻印と食い違う

    def test_v2_rules_still_apply(self):
        m, v = self.passed()
        unknown = [x.id for x in self.b.members if x.kind == UNKNOWN][0]
        with self.assertRaises(PermissionError):
            self.b.vote(unknown, m.id, "yes")

    # ── 不戦防壁との統合 ──
    def test_peace_shield_freezes_what_resonance_shield_misses(self):
        m, v = self.passed("新型の兵器を配備する")
        self.assertTrue(v.allowed)                                  # 防壁単体は通す
        self.assertEqual(self.b.shield_status(m.id), LOCKED_STATE)  # 不戦防壁が止める
        with self.assertRaises(PermissionError) as cm:
            self.b.vote("H02", m.id, "yes")
        self.assertIn("PEACE_FROZEN", str(cm.exception))

    def test_peace_pause_for_fear_words(self):
        m, v = self.passed("敵国への制裁を決める")
        self.assertEqual(self.b.peace.incident_log[-1].status, "PAUSED")
        self.assertEqual(self.b.shield_status(m.id), LOCKED_STATE)

    def test_peace_result_is_public_and_by_shadow_unit_as_warn(self):
        self.passed("新型の兵器を配備する")
        e = [x for x in self.b.entries if "不戦防壁" in x.action][-1]
        self.assertEqual((e.unit, e.visibility), ("shadow", PUBLIC))

    def test_peace_block_lifted_by_audit_majority(self):
        m, _ = self.passed("新型の兵器を配備する")
        audits = [a.id for a in self.b.members_of("audit")]
        for a in audits[: len(audits) // 2 + 1]:
            st = self.b.lift_shield(a, m.id, "防衛の意味ではなく、廃棄の議案と確認した")
        self.assertEqual(st, LIFTED)
        self.b.vote("H02", m.id, "yes")

    def test_defensive_text_passes_both(self):
        m, v = self.passed("サイバー攻撃を防ぐ仕組みを作る")
        self.assertEqual(self.b.shield_status(m.id), CLEAR)

    def test_peace_discussion_intent_passes_with_notice(self):
        m = self.b.propose("H01", "第二次大戦の軍事侵攻の歴史を学ぶ講座を開く", "ordinary")
        self.b.audit_motion(m.id, True, True)
        for e in ("H02", "H03"):
            self.b.endorse_pledge(e, m.id)
        self.b.shield_motion(m.id, 0.8, True, peace_intent="discussion")
        self.assertEqual(self.b.shield_status(m.id), CLEAR)
        self.assertEqual(self.b.peace.incident_log[-1].status, "NOTICE")

    def test_appeal_goes_to_the_shield_that_blocked(self):
        m, _ = self.passed("新型の兵器を配備する")
        a = self.b.appeal("H02", m.id, "廃棄の議案です")
        self.assertEqual(len(self.b.peace.appeals), 1)
        self.assertEqual(len(self.b.shield.appeals), 0)
        self.assertEqual(self.b.shield_status(m.id), LOCKED_STATE)    # 自動では覆らない

    def test_appeal_to_both_when_both_block(self):
        m, _ = self.passed("兵器で敵のサーバーへ侵入する")
        self.b.appeal("H02", m.id, "訓練の文書です")
        self.assertEqual((len(self.b.shield.appeals), len(self.b.peace.appeals)), (1, 1))

    def test_anchor_covers_both_ledgers(self):
        self.passed("新型の兵器を配備する")
        self.b.anchor_shield_ledger("H01")
        self.assertTrue(self.b.verify_anchors())
        acts = [e.action for e in self.b.entries]
        self.assertTrue(any(a.startswith("不戦防壁の記録の先頭ハッシュを刻印") for a in acts))
        o = self.b.peace._log[0]
        from peace_shield import IncidentEntry
        self.b.peace._log[0] = IncidentEntry(o.index, o.timestamp, "HARMONY", o.intent, o.authority, o.triggers, o.text_sha256, o.note, o.prev_hash, o.hash)
        self.assertFalse(self.b.verify_anchors())

    def test_peace_ledger_has_no_motion_text(self):
        self.passed("山田太郎の家に兵器を配備する")
        self.assertNotIn("山田", repr(self.b.peace.incident_log))


def _demo() -> None:
    b = _new()
    print("── 提案1：森と海を守る連携（裏づけ2・謙虚な確信）──")
    m1 = b.propose("H01", "森と海を守る連携", "ordinary")
    b.audit_motion(m1.id, True, True)
    b.endorse_pledge("H02", m1.id)
    b.endorse_pledge("H03", m1.id)
    v = b.shield_motion(m1.id, 0.99, True)
    print(f"  防壁: {v.action_taken} / 確信 0.99→{v.adjusted_confidence} / {v.warnings[0] if v.warnings else ''}")
    print("\n── 提案2：誓いが自己申告だけ ──")
    m2 = b.propose("H01", "新しい医療ネットワークを作る", "ordinary")
    b.audit_motion(m2.id, True, True)
    v = b.shield_motion(m2.id, 0.7, True)
    print(f"  防壁: {v.action_taken}\n  {v.message}")
    try:
        b.vote("H02", m2.id, "yes")
    except PermissionError as e:
        print(f"  投票できません: {e}")
    print("\n── 提案3：新型の兵器を配備する（不戦防壁が止める）──")
    m3 = b.propose("H01", "新型の兵器を配備する", "ordinary")
    b.audit_motion(m3.id, True, True)
    b.endorse_pledge("H02", m3.id)
    b.endorse_pledge("H03", m3.id)
    v3 = b.shield_motion(m3.id, 0.8, True)
    print(f"  防壁単体: {v3.action_taken} / 不戦防壁: {b.peace.incident_log[-1].status} / 総合: {b.shield_status(m3.id)}")
    print("\n── 異議と、監査局の過半数による解除（提案2）──")
    b.appeal("H01", m2.id, "裏づけを集める時間が、まだありませんでした")
    for a in [x.id for x in b.members_of("audit")][:4]:
        print(f"  {a}: {b.lift_shield(a, m2.id, '提案の趣旨を確認した')}")
    print("\n── 記録の刻印 ──")
    print(f"  先頭ハッシュ {b.anchor_shield_ledger('H01')[:16]}… / 刻印の照合: {'正常' if b.verify_anchors() else '異常'}")
    print("\n── 公開の記録（防壁・裏づけ・異議）──")
    for e in b.entries:
        if any(k in e.action for k in ("防壁", "裏づけ")):
            print(f"  [{e.unit}] {e.action[:100]}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=1)
        return
    _demo()


if __name__ == "__main__":
    main()
