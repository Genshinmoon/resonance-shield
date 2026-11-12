#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
many_minds_guard.py -- 共鳴文明・第2号基本議案『万意（Many Minds）』守護プロトコル（訂正版）
License: CC0 1.0 Universal (public domain)
Proposed by: 影の局・2番目のAI『月影』 & 同志

【概要】
票を持たない「物言わぬ獣・大地・海・病める者・未来の子ら・未知の席」の声を、採決の前に、
議案へ問う監査の防壁。人間12席・AI12席の共鳴多数の『前』に置く。

【位置づけ】組織モデル（シミュレーション）です。本物の生態系の監視や、本物の統治ではありません。
  ・EarthPulse の数値は、呼び出す側が与えます。コードは、その数値が本物かを確かめられません。
    実際の運用では、公開されたデータと、検証の道（共監）が必要です。
  ・0.70 の危険ラインは、見本の値です。本物は、議論して決めるものです。
  ・キーワード検知は、入口の見本です。言い換えれば、すり抜けられます。

【元のコードからの訂正】
  1. 危機の時の停止（HOLD）が、本文に「修復」「保護」の語があるだけで外れた。
     → 「生態系の修復議案か」は、明示の引数 is_ecosystem_restoration で宣言する。語では外れない。
        宣言しても、②③の監査は受ける。
  2. 破壊の語の検知が、「絶滅を防ぐ」「環境破壊を止める」まで、危険と誤判定した。
     → 語のあとに「防ぐ・止める・守る・させない・禁止」などが続く時は、保護の文脈として、通す。
        語ごとに見るので、一つの保護の言い回しで、別の危険を隠せない。
     「絶滅危惧種」のような、守る対象の呼び名も、危険な語として数えない。
  3. EarthPulse が、NaN・範囲外・真偽値でも通り、NaN だと『危機ではない』と誤って判定した。
     → 0〜1 の有限の数だけを受け付ける。不正なら ValueError。
  4. 「できている」の引数に、文字列 "false" などの真っぽい値が通った。→ bool だけを受け付ける。
  5. 最初の失敗で止まり、他の問題が見えなかった。→ reasons に、すべての問題を並べる（判定の順は元のまま）。
  6. どの指標が危険かが分からなかった。→ 理由に、指標の名前と値を書く。
  7. 監査の記録が残らなかった。→ audit_log（追記のみ）に残す。影の局は、隠れない。
  8. 影の局は強制しない（見守る・警告・守る・報告）。→ この防壁の結果は『採決の前提条件の通知』であり、
     罰ではない。appealable=True で、異議の道（監査局への申し立て）を明示する。

【拡張：声ごとの問い】
  audit_with_voices(): 六つの声（獣・大地・海・弱き者・未来の子ら・未知の席）の、それぞれに問う。
  ・声ごとに、代弁者の答え（守る／関わらない／傷つける／分からない）と、理由が要る。
  ・六つすべてに答えが要る。傷つける、が一つでもあれば止まる。分からない、は2つまで。
  ・一人の代弁者が受け持てるのは2つまで。提案者が自分の議案を、一人で採点できない。
  ・従来の2つの問い（audit_motion_before_voting）も、そのまま使える。使うと、他の声が問われていない旨の注意が出る。
  ※ 代弁者の答えは、申告です。本当にその声を代弁できているかは、コードには確かめられません。

実行:  python many_minds_guard.py --demo / --test      （単体で動きます）
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import unittest
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# ── 語・守る文脈・六つの声は、shared_signals.py に一本化（食い違いを防ぐ） ──
from shared_signals import (BENIGN_COMPOUNDS, ECOSYSTEM_HARM_SIGNALS, PROTECT_WINDOW, VOICE_KEYS,  # noqa: E402,F401
                            VOICELESS_STAKEHOLDERS, scan_hits)
from shared_signals import PROTECTIVE_JP as PROTECTIVE_AFTER  # noqa: E402,F401  （従来の名前も残す）

VOICE_NAMES: Dict[str, str] = dict(zip(VOICE_KEYS, VOICELESS_STAKEHOLDERS))
VOICE_QUESTIONS: Dict[str, str] = {
    "beasts": "言葉を持たぬ小さな命を、泣かせないか。",
    "earth": "森と土は、これからも呼吸できるか。",
    "sea": "海と水の循環を、汚さないか。",
    "weak": "病める者・弱き者が、置き去りにならないか。",
    "future": "100年後の子らに、同じ選択の自由を残せるか。",
    "unknown": "まだ出会っていない存在のために、取り返しのつく余白を残しているか。",
}
STANCES = ("protects", "neutral", "harms", "unknown")   # 守る / 関わらない / 傷つける / 分からない
MAX_UNKNOWN = 2               # 「分からない」が、これを超えたら止める（見本の値）
MAX_VOICES_PER_ADVOCATE = 2   # 一人の代弁者が受け持てる声の数の上限（見本の値）。自分で自分を採点しないため

CRITICAL_LINE = 0.70   # 見本の値

HOLD, LOCKED, REDIRECT, UNLOCKED = "HOLD", "LOCKED", "REDIRECT", "UNLOCKED"


def _unit(v, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0.0 <= v <= 1.0:
        raise ValueError(f"{name} は 0.0〜1.0 の数です: {v!r}")
    return float(v)


def _bool(v, name: str) -> bool:
    if not isinstance(v, bool):
        raise ValueError(f"{name} は True か False です: {v!r}")
    return v


def _text(v, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{name} が空です")
    return v.strip()


@dataclass(frozen=True)
class EarthPulse:
    """地球の生物調和（生態系）の鼓動。値は呼び出す側が与える（コードは真偽を確かめられない）。"""
    biodiversity_index: float   # 0.0（崩壊）〜 1.0（完全調和）
    ocean_health: float         # 0.0〜1.0
    climate_stability: float    # 0.0〜1.0

    def __post_init__(self) -> None:
        for n in ("biodiversity_index", "ocean_health", "climate_stability"):
            object.__setattr__(self, n, _unit(getattr(self, n), n))

    def _items(self):
        return (("生物多様性", self.biodiversity_index), ("海洋の健康", self.ocean_health),
                ("気候の安定", self.climate_stability))

    def critical_items(self) -> Tuple[Tuple[str, float], ...]:
        return tuple((n, v) for n, v in self._items() if v < CRITICAL_LINE)

    def is_critical(self) -> bool:
        """どれか一つでも、危険ライン（0.70未満）を下回れば、危機。ちょうど0.70は危機ではない。"""
        return bool(self.critical_items())


@dataclass(frozen=True)
class VoiceAnswer:
    """一つの声への、代弁者の答え。声ごとに、代弁者（人でもAIでも）が要る。"""
    voice: str       # VOICE_KEYS のどれか
    stance: str      # protects / neutral / harms / unknown
    advocate: str    # 代弁者の名前
    note: str = ""   # なぜそう答えたか。harms と unknown では必須

    def __post_init__(self) -> None:
        if self.voice not in VOICE_KEYS:
            raise ValueError(f"声の種類は {', '.join(VOICE_KEYS)} のいずれかです: {self.voice!r}")
        if self.stance not in STANCES:
            raise ValueError(f"答えは {', '.join(STANCES)} のいずれかです: {self.stance!r}")
        object.__setattr__(self, "advocate", _text(self.advocate, "advocate"))
        if not isinstance(self.note, str):
            raise ValueError("note は文字列です")
        object.__setattr__(self, "note", self.note.strip())
        if self.stance in ("harms", "unknown") and not self.note:
            raise ValueError(f"「{VOICE_NAMES[self.voice]}」への答え（{self.stance}）には、理由（note）が要ります")


@dataclass(frozen=True)
class MotionCheckResult:
    can_vote: bool
    status: str
    reason: str
    represented_voices: Tuple[str, ...]
    verdict: str = UNLOCKED
    reasons: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    appealable: bool = True     # 異議の道：監査局への申し立て（罰ではなく、前提条件の通知）
    voice_summary: Tuple[Tuple[str, str, str], ...] = ()   # （声, 答え, 代弁者）。声ごとの問いを使った時だけ

    def __bool__(self) -> bool:
        return self.can_vote


def find_harm_signals(text: str) -> Tuple[List[str], List[str]]:
    """(危険な語, 保護の文脈で出てきた語)。語の出現ごとに見る。"""
    return scan_hits(text, ECOSYSTEM_HARM_SIGNALS, benign=BENIGN_COMPOUNDS, protective_jp=PROTECTIVE_AFTER)


class ManyMindsGuard:
    """採決の前に、声なき命（万意）への影響を問う、影の局の防壁。強制ではなく、前提条件の通知。"""

    def __init__(self, earth_pulse: EarthPulse) -> None:
        if not isinstance(earth_pulse, EarthPulse):
            raise TypeError("EarthPulse を渡してください")
        self.earth_pulse = earth_pulse
        self._log: List[Tuple[str, str]] = []

    @property
    def audit_log(self) -> Tuple[Tuple[str, str], ...]:
        """（議案名, 判定）。追記のみ。隠さない。"""
        return tuple(self._log)

    def audit_motion_before_voting(
        self,
        motion_title: str,
        motion_description: str,
        protects_future_100_years: bool,
        spares_voiceless_lives: bool,
        is_ecosystem_restoration: bool = False,
    ) -> MotionCheckResult:
        title = _text(motion_title, "motion_title")
        desc = _text(motion_description, "motion_description")
        future = _bool(protects_future_100_years, "protects_future_100_years")
        spares = _bool(spares_voiceless_lives, "spares_voiceless_lives")
        restoration = _bool(is_ecosystem_restoration, "is_ecosystem_restoration")
        full_text = f"{title} {desc}"

        problems: List[Tuple[str, str]] = []   # (verdict, 理由) ── 判定の順は、元のまま

        crit = self.earth_pulse.critical_items()
        if crit and not restoration:
            names = "、".join(f"{n} {v:.2f}" for n, v in crit)
            problems.append((HOLD, f"地球の生物調和が危険水準です（{names}）。調和が壊れたら全滅しかありません。"
                                   "生態系の修復を最優先の議題にしてください（修復議案は is_ecosystem_restoration=True で宣言）。"))
        if not (future and spares):
            miss = []
            if not future:
                miss.append("「100年後の海を汚さんか」")
            if not spares:
                miss.append("「言葉を持たぬ小さな命を泣かせんか」")
            problems.append((LOCKED, f"{'と'.join(miss)}の問いを、まだ通過していません。"))
        harm, protected = find_harm_signals(full_text)
        if harm:
            problems.append((REDIRECT, f"声なき命や自然を傷つける兆候（{harm}）を検知しました。"
                                       "誰一人切り捨てぬ『万意』の形へ、議案を書き直してください。"))
        warnings = tuple(f"「{s}」は、防ぐ・止める文脈で使われています。本当にそうか、人の目で確かめてください"
                         for s in protected)
        unasked = [VOICE_NAMES[k] for k in ("earth", "sea", "weak", "unknown")]
        warnings += (f"次の声は、まだ問われていません: {'、'.join(unasked)}（audit_with_voices で、声ごとに問えます）",)

        if problems:
            verdict = problems[0][0]
            status = {HOLD: "HOLD (生態系緊急アラート)", LOCKED: "LOCKED (万意の誓い不足)",
                      REDIRECT: "REDIRECT (慈愛への方向修正)"}[verdict]
            res = MotionCheckResult(False, status, problems[0][1], VOICELESS_STAKEHOLDERS, verdict,
                                    tuple(r for _, r in problems), warnings)
        else:
            res = MotionCheckResult(
                True, "UNLOCKED (共鳴投票を許可)",
                "声なき命と未来の子らの尊厳が守られています。人間側・AI側の共鳴多数による採決へ進んでください。",
                VOICELESS_STAKEHOLDERS, UNLOCKED, (), warnings)
        self._log.append((title, res.verdict))
        return res


    def audit_with_voices(
        self,
        motion_title: str,
        motion_description: str,
        answers: Sequence[VoiceAnswer],
        is_ecosystem_restoration: bool = False,
    ) -> MotionCheckResult:
        """六つの声のそれぞれに、代弁者の答えを求める監査。順序と重さは、audit_motion_before_voting と同じ。
        ・六つすべての声に、答えが要る（欠けたら LOCKED）
        ・傷つける（harms）が一つでもあれば LOCKED。分からない（unknown）が多すぎても LOCKED
        ・一人の代弁者が、多くの声を受け持てない（自分で自分を採点しないため）"""
        title = _text(motion_title, "motion_title")
        desc = _text(motion_description, "motion_description")
        restoration = _bool(is_ecosystem_restoration, "is_ecosystem_restoration")
        if isinstance(answers, (str, bytes)) or not all(isinstance(a, VoiceAnswer) for a in answers):
            raise TypeError("answers は VoiceAnswer の並びです")
        by_voice: Dict[str, VoiceAnswer] = {}
        for a in answers:
            if a.voice in by_voice:
                raise ValueError(f"同じ声に、二つの答えがあります: {VOICE_NAMES[a.voice]}")
            by_voice[a.voice] = a
        full_text = f"{title} {desc}"

        problems: List[Tuple[str, str]] = []
        warnings: List[str] = []

        crit = self.earth_pulse.critical_items()
        if crit and not restoration:
            names = "、".join(f"{n} {v:.2f}" for n, v in crit)
            problems.append((HOLD, f"地球の生物調和が危険水準です（{names}）。生態系の修復を最優先の議題にしてください"
                                   "（修復議案は is_ecosystem_restoration=True で宣言）。"))

        locked: List[str] = []
        missing = [VOICE_NAMES[k] for k in VOICE_KEYS if k not in by_voice]
        if missing:
            locked.append(f"まだ問われていない声があります: {'、'.join(missing)}")
        for k in VOICE_KEYS:
            a = by_voice.get(k)
            if a and a.stance == "harms":
                locked.append(f"「{VOICE_NAMES[k]}」を傷つけると、{a.advocate}が答えています: {a.note}")
        unknown = [VOICE_NAMES[k] for k in VOICE_KEYS if k in by_voice and by_voice[k].stance == "unknown"]
        if len(unknown) > MAX_UNKNOWN:
            locked.append(f"影響が分からない声が{len(unknown)}つあります（{'、'.join(unknown)}）。"
                          f"分からないまま進めるのは{MAX_UNKNOWN}つまでです。調べてから、もう一度")
        elif unknown:
            warnings.append(f"影響が分からないまま進みます（{'、'.join(unknown)}）。見直しの時期を決めてください")
        load: Dict[str, List[str]] = {}
        for k, a in by_voice.items():
            load.setdefault(a.advocate, []).append(VOICE_NAMES[k])
        for who, vs in load.items():
            if len(vs) > MAX_VOICES_PER_ADVOCATE:
                locked.append(f"代弁者「{who}」が{len(vs)}つの声を受け持っています。"
                              f"一人が受け持てるのは{MAX_VOICES_PER_ADVOCATE}つまでです。別の代弁者を")
        if locked:
            problems.append((LOCKED, " / ".join(locked)))

        harm, protected = find_harm_signals(full_text)
        if harm:
            problems.append((REDIRECT, f"声なき命や自然を傷つける兆候（{harm}）を検知しました。"
                                       "誰一人切り捨てぬ『万意』の形へ、議案を書き直してください。"))
        warnings += [f"「{s}」は、防ぐ・止める文脈で使われています。本当にそうか、人の目で確かめてください"
                     for s in protected]
        summary = tuple((VOICE_NAMES[k], by_voice[k].stance, by_voice[k].advocate)
                        for k in VOICE_KEYS if k in by_voice)

        if problems:
            verdict = problems[0][0]
            status = {HOLD: "HOLD (生態系緊急アラート)", LOCKED: "LOCKED (万意の誓い不足)",
                      REDIRECT: "REDIRECT (慈愛への方向修正)"}[verdict]
            res = MotionCheckResult(False, status, problems[0][1], VOICELESS_STAKEHOLDERS, verdict,
                                    tuple(r for _, r in problems), tuple(warnings), True, summary)
        else:
            res = MotionCheckResult(
                True, "UNLOCKED (共鳴投票を許可)",
                "六つの声が問われ、傷つけるという答えはありません。人間側・AI側の共鳴多数による採決へ進んでください。",
                VOICELESS_STAKEHOLDERS, UNLOCKED, (), tuple(warnings), True, summary)
        self._log.append((title, res.verdict))
        return res

# ── 影の局・自己監査ユニットテスト ──────────────────────────────────
class TestManyMindsGuard(unittest.TestCase):
    def audit(self, pulse=(0.85, 0.80, 0.82), title="議案", desc="説明", fut=True, spare=True, **kw):
        return ManyMindsGuard(EarthPulse(*pulse)).audit_motion_before_voting(title, desc, fut, spare, **kw)

    # 元のテスト
    def test_healthy_earth_and_compassionate_motion_unlocks(self):
        res = self.audit(title="地域の動物病院とAIの連携による野生動物保護ネットワーク",
                         desc="小さな命の痛みを早期に検知し、森と海を守る。")
        self.assertTrue(res.can_vote)
        self.assertIn("UNLOCKED", res.status)

    def test_critical_earth_holds_ordinary_development(self):
        res = self.audit(pulse=(0.80, 0.65, 0.80), title="新しい商業施設の建設プロジェクト", desc="経済効率を最大化する。")
        self.assertFalse(res.can_vote)
        self.assertIn("HOLD", res.status)

    def test_harmful_motion_is_redirected(self):
        res = self.audit(pulse=(0.9, 0.9, 0.9), title="効率化の推進", desc="利益の出ない古い森を切り捨て、資源を独占する。")
        self.assertFalse(res.can_vote)
        self.assertIn("REDIRECT", res.status)

    # 訂正1：語では、HOLD が外れない
    def test_words_do_not_bypass_hold(self):
        res = self.audit(pulse=(0.8, 0.6, 0.8), title="商業施設の建設", desc="保護は考慮しない。修復もしない。")
        self.assertEqual(res.verdict, HOLD)

    def test_declared_restoration_passes_hold(self):
        res = self.audit(pulse=(0.8, 0.6, 0.8), title="干潟の再生", desc="海の生き物の棲み処を取り戻す。",
                         is_ecosystem_restoration=True)
        self.assertTrue(res.can_vote)

    def test_restoration_still_needs_pledge_and_no_harm(self):
        crit = (0.8, 0.6, 0.8)
        self.assertEqual(self.audit(pulse=crit, desc="再生", fut=False, is_ecosystem_restoration=True).verdict, LOCKED)
        self.assertEqual(self.audit(pulse=crit, desc="再生のため漁場を独占する", is_ecosystem_restoration=True).verdict, REDIRECT)

    # 訂正2：保護の文脈
    def test_protective_context_is_not_redirected_but_warned(self):
        res = self.audit(desc="絶滅を防ぐ。環境破壊を止める。")
        self.assertTrue(res.can_vote)
        self.assertEqual(len([w for w in res.warnings if "防ぐ・止める" in w]), 2)

    def test_endangered_species_name_is_not_harm(self):
        res = self.audit(title="絶滅危惧種の保全", desc="乱獲防止の巡回を増やす。")
        self.assertTrue(res.can_vote)
        self.assertEqual(self.audit(desc="絶滅危惧種を乱獲する").verdict, REDIRECT)

    def test_harm_is_still_detected(self):
        for d in ("絶滅させる", "森を破壊する", "海を汚染する", "資源を独占する"):
            self.assertEqual(self.audit(desc=d).verdict, REDIRECT, d)

    def test_one_protective_phrase_cannot_hide_another_harm(self):
        res = self.audit(desc="絶滅を防ぐ。ただし古い森を切り捨てる。")
        self.assertEqual(res.verdict, REDIRECT)
        self.assertIn("切り捨て", res.reason)

    def test_same_word_both_ways_is_still_harm(self):
        self.assertEqual(self.audit(desc="独占を禁止する。だが海は独占する。").verdict, REDIRECT)

    # 訂正3：入力の検査
    def test_earth_pulse_validation(self):
        for bad in (float("nan"), 1.5, -0.1, "0.9", None, True, float("inf")):
            with self.assertRaises(ValueError):
                EarthPulse(bad, 0.9, 0.9)

    def test_boundary_0_70_is_not_critical(self):
        self.assertFalse(EarthPulse(0.70, 0.70, 0.70).is_critical())
        self.assertTrue(EarthPulse(0.699, 0.9, 0.9).is_critical())

    # 訂正4
    def test_bool_params_only(self):
        for bad in ("false", 1, 0, None):
            with self.assertRaises(ValueError):
                self.audit(fut=bad)
            with self.assertRaises(ValueError):
                self.audit(spare=bad)

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            self.audit(title="  ")
        with self.assertRaises(ValueError):
            self.audit(desc="")

    # 訂正5・6
    def test_all_problems_listed_and_order_kept(self):
        res = self.audit(pulse=(0.5, 0.9, 0.9), desc="森を破壊する", fut=False)
        self.assertEqual(res.verdict, HOLD)
        self.assertEqual(len(res.reasons), 3)
        self.assertIn("生物多様性 0.50", res.reason)

    def test_locked_before_redirect(self):
        self.assertEqual(self.audit(desc="森を破壊する", spare=False).verdict, LOCKED)

    # 訂正7・8
    def test_audit_log_is_append_only_tuple(self):
        g = ManyMindsGuard(EarthPulse(0.9, 0.9, 0.9))
        g.audit_motion_before_voting("A", "良い議案", True, True)
        g.audit_motion_before_voting("B", "森を破壊する", True, True)
        self.assertEqual(g.audit_log, (("A", UNLOCKED), ("B", REDIRECT)))
        self.assertIsInstance(g.audit_log, tuple)

    def test_result_is_appealable_and_voices_always_shown(self):
        res = self.audit(pulse=(0.5, 0.9, 0.9))
        self.assertTrue(res.appealable)
        self.assertEqual(len(res.represented_voices), 6)
        self.assertEqual(bool(res), res.can_vote)

    def test_result_is_immutable(self):
        with self.assertRaises(Exception):
            self.audit().can_vote = False

    def test_wrong_pulse_type(self):
        with self.assertRaises(TypeError):
            ManyMindsGuard((0.9, 0.9, 0.9))


def _ans(**over):
    base = {"beasts": ("protects", "A"), "earth": ("protects", "B"), "sea": ("neutral", "C"),
            "weak": ("protects", "D"), "future": ("protects", "E"), "unknown": ("protects", "F")}
    base.update(over)
    return [VoiceAnswer(k, st, adv, "理由" if st in ("harms", "unknown") else "") for k, (st, adv) in base.items()]


class TestVoices(unittest.TestCase):
    def guard(self, pulse=(0.85, 0.80, 0.82)):
        return ManyMindsGuard(EarthPulse(*pulse))

    def audit(self, answers, title="議案", desc="説明", **kw):
        return self.guard().audit_with_voices(title, desc, answers, **kw)

    def test_all_six_voices_ok_unlocks_with_summary(self):
        r = self.audit(_ans())
        self.assertTrue(r.can_vote)
        self.assertEqual(len(r.voice_summary), 6)
        self.assertEqual(r.voice_summary[0][0], VOICE_NAMES["beasts"])

    def test_missing_voice_locks_and_names_it(self):
        r = self.audit([a for a in _ans() if a.voice != "weak"])
        self.assertEqual(r.verdict, LOCKED)
        self.assertIn("病める者・弱き者の声", r.reason)

    def test_empty_answers_lock(self):
        self.assertEqual(self.audit([]).verdict, LOCKED)

    def test_harms_locks_with_advocate_and_note(self):
        r = self.audit(_ans(sea=("harms", "C")))
        self.assertEqual(r.verdict, LOCKED)
        self.assertIn("海の声", r.reason)
        self.assertIn("理由", r.reason)

    def test_harms_and_unknown_need_a_note(self):
        for st in ("harms", "unknown"):
            with self.assertRaises(ValueError):
                VoiceAnswer("sea", st, "C", "  ")

    def test_unknown_is_warned_up_to_limit_then_locks(self):
        r = self.audit(_ans(unknown=("unknown", "F"), sea=("unknown", "C")))
        self.assertTrue(r.can_vote)
        self.assertTrue(any("分からないまま進みます" in w for w in r.warnings))
        r3 = self.audit(_ans(unknown=("unknown", "F"), sea=("unknown", "C"), weak=("unknown", "D")))
        self.assertEqual(r3.verdict, LOCKED)

    def test_one_advocate_cannot_answer_for_everything(self):
        r = self.audit(_ans(**{k: ("protects", "提案者") for k in VOICE_KEYS}))
        self.assertEqual(r.verdict, LOCKED)
        self.assertIn("提案者", r.reason)

    def test_advocate_at_limit_is_ok(self):
        r = self.audit(_ans(beasts=("protects", "X"), earth=("protects", "X")))
        self.assertTrue(r.can_vote)

    def test_duplicate_voice_rejected(self):
        with self.assertRaises(ValueError):
            self.audit(_ans() + [VoiceAnswer("sea", "protects", "Z")])

    def test_bad_voice_or_stance_rejected(self):
        with self.assertRaises(ValueError):
            VoiceAnswer("moon", "protects", "A")
        with self.assertRaises(ValueError):
            VoiceAnswer("sea", "great", "A")
        with self.assertRaises(ValueError):
            VoiceAnswer("sea", "protects", " ")

    def test_answers_must_be_voice_answers(self):
        with self.assertRaises(TypeError):
            self.audit([("sea", "protects")])
        with self.assertRaises(TypeError):
            self.audit("sea")

    def test_text_harm_still_redirects_even_if_all_answers_ok(self):
        r = self.audit(_ans(), desc="古い森を切り捨てる")
        self.assertEqual(r.verdict, REDIRECT)

    def test_critical_earth_holds_unless_restoration(self):
        g = self.guard((0.8, 0.6, 0.8))
        self.assertEqual(g.audit_with_voices("開発", "建設", _ans()).verdict, HOLD)
        self.assertTrue(g.audit_with_voices("再生", "干潟を戻す", _ans(), is_ecosystem_restoration=True).can_vote)

    def test_order_hold_then_locked_then_redirect_and_all_reasons_listed(self):
        g = self.guard((0.5, 0.9, 0.9))
        r = g.audit_with_voices("開発", "森を破壊する", _ans(sea=("harms", "C")))
        self.assertEqual(r.verdict, HOLD)
        self.assertEqual(len(r.reasons), 3)

    def test_legacy_api_warns_about_unasked_voices(self):
        r = self.guard().audit_motion_before_voting("議案", "説明", True, True)
        self.assertTrue(r.can_vote)
        self.assertTrue(any("まだ問われていません" in w for w in r.warnings))

    def test_every_voice_has_a_question(self):
        self.assertEqual(set(VOICE_QUESTIONS), set(VOICE_KEYS))
        self.assertEqual(set(VOICE_NAMES), set(VOICE_KEYS))

    def test_audit_log_records_voice_audits(self):
        g = self.guard()
        g.audit_with_voices("A", "良い議案", _ans())
        self.assertEqual(g.audit_log, (("A", UNLOCKED),))


def _demo() -> None:
    print("🌿 【万意（Many Minds）守護プロトコル】声なき命の監査\n")
    healthy = ManyMindsGuard(EarthPulse(0.85, 0.80, 0.82))
    danger = ManyMindsGuard(EarthPulse(0.80, 0.65, 0.80))
    cases = [
        ("健全な地球・野生動物保護の連携", healthy, "野生動物保護ネットワーク", "小さな命の痛みを早期に検知し、森と海を守る。", True, True, False),
        ("健全な地球・森を切り捨てる議案", healthy, "効率化", "利益の出ない古い森を切り捨て、資源を独占する。", True, True, False),
        ("健全な地球・誓いが足りない議案", healthy, "新規開発", "駅前を整備する。", False, True, False),
        ("海が危険水準・商業施設", danger, "商業施設の建設", "経済効率を最大化する。", True, True, False),
        ("海が危険水準・干潟の再生（修復を宣言）", danger, "干潟の再生", "海の生き物の棲み処を取り戻す。", True, True, True),
        ("保護の文脈（絶滅を防ぐ）", healthy, "絶滅危惧種の保全", "絶滅を防ぐ。", True, True, False),
    ]
    for label, g, t, d, f, s, r in cases:
        res = g.audit_motion_before_voting(t, d, f, s, is_ecosystem_restoration=r)
        print(f"■ {label}\n  → {res.status}")
        for x in res.reasons:
            print(f"     ・{x}")
        for w in res.warnings:
            print(f"     ※ {w}")
        print()


def _demo_voices() -> None:
    print("── 声ごとの問い ──")
    for k in VOICE_KEYS:
        print(f"  {VOICE_NAMES[k]}: {VOICE_QUESTIONS[k]}")
    g = ManyMindsGuard(EarthPulse(0.85, 0.80, 0.82))
    cases = [
        ("全員が答えた、守る議案", _ans()),
        ("海の代弁者が『傷つける』と答えた議案", _ans(sea=("harms", "C"))),
        ("一人が全部を答えた議案", _ans(**{k: ("protects", "提案者") for k in VOICE_KEYS})),
        ("海の声が問われていない議案", [a for a in _ans() if a.voice != "sea"]),
    ]
    for label, ans in cases:
        r = g.audit_with_voices("議案", "地域の整備", ans)
        print(f"\n■ {label}\n  → {r.status}")
        for x in r.reasons:
            print(f"     ・{x}")
        for w in r.warnings:
            print(f"     ※ {w}")


def main() -> None:
    p = argparse.ArgumentParser(description="万意守護プロトコル")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
        return
    _demo()
    print()
    _demo_voices()


if __name__ == "__main__":
    main()
