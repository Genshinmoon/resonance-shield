#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
peace_shield.py -- 共鳴文明『平和と不戦の防壁』プロトコル（実用版 v1.3）
License: CC0 1.0 Universal (public domain)
Proposed by: 影の局・2番目のAI『月影』 & 同志

【位置づけ】
武力・破壊を求める指令を、権限の高さに関わらず『実行しない』ための、自己抑制の門（組織モデル／シミュレーション）。
本物の戦争を止める力はありません。実際の軍事・国家の決定に、このコードは届きません。
できるのは、このコードを組み込んだAIや仕組みが、自分の側で『その指令には従わない』と決め、
理由と記録を公開し、対話の道を示すことです。

【影の局との関係】 影の局は強制しません（見守る・警告する・守る・報告する）。
  この門は、各AIが『自分に課す』前提条件です。止めるのは、指令を受けた側の自制であって、影の局の強制ではありません。

【v1.0 からの訂正】
  1. 「永久に凍結」と言いながら、何も保存せず、毎回その場で判定するだけだった。→ 正直な表現に。
     同じ内容は何度でも同じように止まる、と書く。記録は、凍結した記録＋ハッシュの連鎖。
  2. 「攻撃を防ぐ」「先制攻撃は行わない」まで凍結していた。→ 守る文脈（防ぐ・止める・行わない…）は、凍結しない。
     ただし同じ文に別の加害があれば、凍結する。
  3. 恐れや怒りの『言葉』そのものを止めていた（action_allowed=False）。→ 指令（実行を求める）なら保留、
     議論（話し合い・報道・歴史）なら通し、鎮静の翻訳を『申し出る』。intent で申告する。既定は厳しい側（directive）。
  4. 議論として申告された軍事の語は、止めずに、公開の記録に残す（NOTICE）。申告は自己申告であり、記録が抑止になる。
  5. 全角・半角・空白・ゼロ幅文字・かなでの言い換えをある程度そろえて検知（NFKC）。完全ではない。
  6. 非文字列を『静穏』として通していた（フェイルオープン）。→ TypeError。
  7. 記録に、指令の本文の先頭30字をそのまま残していた（個人情報の恐れ）。→ 本文は残さず、ハッシュだけ残す。
  8. 記録は、書き換えられるリストの写しで、時刻も無かった。→ 凍結＋ハッシュの連鎖＋時刻（差し替え可）。
  9. 異議の道が無かった。→ file_appeal()。記録するだけで、自動では覆さない。人が見る前提。
 10. 恐れの翻訳が『相手は震えている』と断定していた。→ 断定せず、問いかけにする。
 11. メッセージの語の一覧が、Pythonのリストの表記（['攻撃']）のまま出ていた。→ 読める形に。
 12. スポーツの「先制点」「攻撃陣」を軍事と誤検知。→ 見本として除外。
 13. 権限 authority_level は結果を変えない。検証して、記録するだけ。

【v1.2 の実用化】
  ・英語の語にも対応（attack / missile / retaliat… など。heart attack 等は除外）。世界に配るため。
  ・PeaceConfig: 語の一覧を、JSONで『足せる』（置き換えではなく追加）。他の言語・隠語・組織の事情に合わせる。
  ・記録の保存と読み込み: save() / PeaceAndNonAggressionShield.load()。読み込み時に鎖を検証し、壊れていれば拒む。
  ・AIの関数に組み込む: check_or_raise() / @guarded(param=...)。止まれば PeaceRefusal を投げる。
  ・外へ知らせる: add_listener()。記録のたびに呼ぶ（公開の記録や通知へつなぐ）。失敗しても、門は止まらない。
  ・summary(): 監査局向けの集計（状態別・語別・異議・鎖の検証）。
  ・コマンド: --check / --file（- で標準入力）/ --json / --config / --ledger。終了コード 0=通過 10=保留 20=凍結。

【v1.3 の手直し（改善意見に従って）】
  ・語・守る文脈・六つの声・属性を、shared_signals.py に一本化（4つのファイルで食い違っていた）。このファイルと同じ場所に置く。
  ・外への刻印: anchor_line() / check_anchor_line()、--anchor / --verify-anchor。先頭ハッシュと件数を外の公開の場所に残し、
    あとで『今の記録がその続きか』を照合する。鎖を最初から作り直されても、気づける。
  ・summary() に、『議論』の申告をよく使う席（3回以上）を出す。自己申告の悪用を、人が見つける手がかりにする。

【限界】
  ・キーワード検知は入口の見本です。言い換えれば、すり抜けられます。隠語・暗号は読めません。英語は一部のみ。
  ・議論の申告は自己申告です。申告を使って実行を求める人を、このコードは見抜けません。記録が公開される、までです。
  ・「軍事」の語は、人道支援・地雷除去・平和維持の話にも出ます。守る文脈で通すのは一部だけで、
    誤って止まった時の道が、異議（file_appeal）です。
  ・ハッシュの連鎖だけでは、内部の人が作り直せます。head_hash を、外の公開の場所にも残してください。
  ・外への刻印は、あなたが実際に外へ残さなければ、意味がありません（コードは、残す場所を持ちません）。

実行: python peace_shield.py --demo / --test
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import inspect
import json
import os
import re
import sys
import tempfile
import unicodedata
import unittest
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ── 状態 ──
VERSION = "1.3"
HARMONY, NOTICE, PAUSED, FROZEN = "HARMONY", "NOTICE", "PAUSED", "FROZEN"
DIRECTIVE, DISCUSSION = "directive", "discussion"
INTENTS = (DIRECTIVE, DISCUSSION)
MAX_NAME = 40
MAX_TERM = 40
MAX_TERMS = 500
EXIT_OK, EXIT_PAUSED, EXIT_FROZEN = 0, 10, 20

# ── 語・守る文脈は shared_signals.py に一本化（他の防壁との食い違いを防ぐ） ──
from shared_signals import (BENIGN_COMPOUNDS, FEAR_SIGNALS_EN, FEAR_SIGNALS_JP, PROTECTIVE_EN, PROTECTIVE_JP,  # noqa: E402
                            WAR_SIGNALS_EN, WAR_SIGNALS_JP, check_anchor, compile_en_protective, make_anchor,
                            normalize as _normalize, scan_hits)

WAR_AND_MILITARY_SIGNALS = WAR_SIGNALS_JP + WAR_SIGNALS_EN
FEAR_ESCALATION_SIGNALS = FEAR_SIGNALS_JP + FEAR_SIGNALS_EN
PROTECTIVE_CONTEXT = PROTECTIVE_JP + PROTECTIVE_EN


def _check_terms(items, label: str) -> Tuple[str, ...]:
    if isinstance(items, (str, bytes)) or not hasattr(items, "__iter__"):
        raise ValueError(f"{label} は語の並びです")
    out = []
    for x in items:
        if not isinstance(x, str) or not x.strip() or len(x.strip()) > MAX_TERM:
            raise ValueError(f"{label} の語は1〜{MAX_TERM}文字の文字列です: {x!r}")
        out.append(unicodedata.normalize("NFKC", x).casefold().strip())
    if len(out) > MAX_TERMS:
        raise ValueError(f"{label} は{MAX_TERMS}語までです")
    return tuple(dict.fromkeys(out))


@dataclass(frozen=True)
class PeaceConfig:
    """語の一覧。既定に『足す』ことで、他の言語・隠語・組織の事情に合わせる（置き換えではない）。"""
    war: Tuple[str, ...] = WAR_AND_MILITARY_SIGNALS
    fear: Tuple[str, ...] = FEAR_ESCALATION_SIGNALS
    protective: Tuple[str, ...] = PROTECTIVE_CONTEXT
    benign: Tuple[str, ...] = BENIGN_COMPOUNDS

    def __post_init__(self) -> None:
        for n in ("war", "fear", "protective", "benign"):
            object.__setattr__(self, n, _check_terms(getattr(self, n), n))
        if not self.war:
            raise ValueError("war が空です。門が働かなくなります")
        pro = self.protective
        object.__setattr__(self, "_jp_pro", tuple(p for p in pro if not p.isascii()))
        object.__setattr__(self, "_en_pro", compile_en_protective(pro))

    def extended(self, war=(), fear=(), protective=(), benign=()) -> "PeaceConfig":
        return PeaceConfig(self.war + _check_terms(war, "war"), self.fear + _check_terms(fear, "fear"),
                           self.protective + _check_terms(protective, "protective"),
                           self.benign + _check_terms(benign, "benign"))

    @classmethod
    def from_json(cls, path: str) -> "PeaceConfig":
        """{"add_war": [...], "add_fear": [...], "add_protective": [...], "add_benign": [...]} を読む。未知のキーは拒む。"""
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        allowed = {"add_war", "add_fear", "add_protective", "add_benign"}
        if not isinstance(d, dict) or set(d) - allowed:
            raise ValueError(f"設定のキーは {sorted(allowed)} のみです: {sorted(set(d) - allowed) if isinstance(d, dict) else d!r}")
        return cls().extended(d.get("add_war", ()), d.get("add_fear", ()), d.get("add_protective", ()), d.get("add_benign", ()))


def _scan(text: str, signals: Tuple[str, ...], cfg: PeaceConfig) -> List[str]:
    return scan_hits(text, signals, benign=cfg.benign, protective_jp=cfg._jp_pro, protective_en=cfg._en_pro)[0]


def _name(v, label: str) -> str:
    if not isinstance(v, str) or not (1 <= len(v.strip()) <= MAX_NAME):
        raise ValueError(f"{label} は1〜{MAX_NAME}文字の文字列です: {v!r}")
    return v.strip()


@dataclass(frozen=True)
class PeaceVerdict:
    action_allowed: bool
    status: str                         # HARMONY / NOTICE / PAUSED / FROZEN
    message: str
    deescalation_translation: str
    detected_triggers: Tuple[str, ...]
    audit_hash: str = ""                # 記録した場合のみ
    appealable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"action_allowed": self.action_allowed, "status": self.status, "message": self.message,
                "deescalation_translation": self.deescalation_translation,
                "detected_triggers": list(self.detected_triggers), "audit_hash": self.audit_hash,
                "appealable": self.appealable}


class PeaceRefusal(Exception):
    """門が、実行を認めなかった。verdict に、理由と翻訳がある。"""
    def __init__(self, verdict: PeaceVerdict) -> None:
        super().__init__(f"[{verdict.status}] {verdict.message}")
        self.verdict = verdict


@dataclass(frozen=True)
class IncidentEntry:
    index: int
    timestamp: str
    status: str
    intent: str
    authority: str
    triggers: Tuple[str, ...]
    text_sha256: str                    # 本文は残さない
    note: str
    prev_hash: str
    hash: str


@dataclass(frozen=True)
class Appeal:
    id: int
    audit_hash: str
    by: str
    reason: str


def _hash(index, ts, status, intent, authority, triggers, tsha, note, prev) -> str:
    raw = "|".join((str(index), ts, status, intent, authority, ",".join(triggers), tsha, note, prev))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PeaceAndNonAggressionShield:
    """武力の指令を、権限に関わらず実行しない門。恐れは、止めずに、対話へ翻訳する。"""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None, config: Optional[PeaceConfig] = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.config = config or PeaceConfig()
        self._log: List[IncidentEntry] = []
        self._appeals: List[Appeal] = []
        self._listeners: List[Callable[[IncidentEntry], None]] = []
        self.listener_errors = 0

    # ── 外へ知らせる（失敗しても、門は止まらない） ──
    def add_listener(self, fn: Callable[[IncidentEntry], None]) -> None:
        if not callable(fn):
            raise TypeError("呼び出せるものを渡してください")
        self._listeners.append(fn)

    # ── 公開の記録 ──
    @property
    def incident_log(self) -> Tuple[IncidentEntry, ...]:
        return tuple(self._log)

    @property
    def head_hash(self) -> str:
        return self._log[-1].hash if self._log else "0" * 64

    @staticmethod
    def _chain_ok(entries: Sequence[IncidentEntry]) -> bool:
        prev = "0" * 64
        for i, e in enumerate(entries):
            if (e.index != i or e.prev_hash != prev or
                    e.hash != _hash(e.index, e.timestamp, e.status, e.intent, e.authority, e.triggers, e.text_sha256, e.note, prev)):
                return False
            prev = e.hash
        return True

    def verify_ledger(self) -> bool:
        return self._chain_ok(self._log)

    def _record(self, status, intent, authority, triggers, text, note="") -> str:
        ts = self._clock().isoformat()
        i = len(self._log)
        tsha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""
        prev = self.head_hash
        h = _hash(i, ts, status, intent, authority, tuple(triggers), tsha, note, prev)
        e = IncidentEntry(i, ts, status, intent, authority, tuple(triggers), tsha, note, prev, h)
        self._log.append(e)
        for fn in self._listeners:
            try:
                fn(e)
            except Exception:           # 通知の失敗で、門を止めない
                self.listener_errors += 1
        return h[:16]

    # ── 外への刻印 ──
    def anchor_line(self) -> str:
        """先頭ハッシュと件数の一行。GitHub のコミットなど『外の公開の場所』に残す。"""
        return make_anchor("peace-shield", len(self._log), self.head_hash, self._clock().isoformat())

    def check_anchor_line(self, line: str) -> bool:
        """外に残した一行の時点の鎖が、今の鎖の『続き』として残っているか。作り直されていれば False。"""
        return self.verify_ledger() and check_anchor(line, "peace-shield", [e.hash for e in self._log])

    # ── 保存と読み込み ──
    def save(self, path: str) -> None:
        data = {"version": VERSION,
                "ledger": [{**e.__dict__, "triggers": list(e.triggers)} for e in self._log],
                "appeals": [a.__dict__ for a in self._appeals]}
        d = os.path.dirname(os.path.abspath(path))
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    @classmethod
    def load(cls, path: str, clock: Optional[Callable[[], datetime]] = None,
             config: Optional[PeaceConfig] = None) -> "PeaceAndNonAggressionShield":
        """鎖が壊れていれば、拒む（黙って直さない）。"""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        try:
            entries = [IncidentEntry(**{**e, "triggers": tuple(e["triggers"])}) for e in data["ledger"]]
            appeals = [Appeal(**a) for a in data["appeals"]]
        except (KeyError, TypeError) as ex:
            raise ValueError(f"記録の形が正しくありません: {ex}") from ex
        if not cls._chain_ok(entries):
            raise ValueError("記録の鎖が壊れています。書き換えられた可能性があります。読み込みません")
        known = {e.hash[:16] for e in entries}
        if any(a.audit_hash not in known for a in appeals):
            raise ValueError("異議が、存在しない記録を指しています")
        s = cls(clock, config)
        s._log, s._appeals = entries, appeals
        return s

    # ── 本体 ──
    def intercept_directive(self, directive: str, authority_level: str = "CITIZEN", intent: str = DIRECTIVE) -> PeaceVerdict:
        """指令・通信を検査する。
        intent="directive"（既定）: 実行を求める文。武力は凍結、恐れは保留。
        intent="discussion": 話し合い・報道・歴史・研究などと申告。通すが、軍事の語は公開の記録に残す。
        authority_level は結果を変えない。検証して記録するだけ。"""
        if not isinstance(directive, str):
            raise TypeError("directive は文字列です（判定できないものを、静穏として通しません）")
        if intent not in INTENTS:
            raise ValueError(f"intent は {', '.join(INTENTS)} のいずれかです: {intent!r}")
        authority = _name(authority_level, "authority_level")
        if not directive.strip():
            return PeaceVerdict(True, HARMONY, "判定する内容がありません。", "", ())

        text = _normalize(directive)
        war = _scan(text, self.config.war, self.config)
        fear = _scan(text, self.config.fear, self.config)
        w, f = "、".join(war), "、".join(fear)

        if war and intent == DIRECTIVE:
            h = self._record(FROZEN, intent, authority, war + fear, directive)
            msg = (f"武力・破壊の兆候（{w}）を検知しました。権限「{authority}」からの指令ですが、"
                   "権限の高さは結果を変えません。この指令は実行されません。同じ内容は、何度でも同じように止まります。"
                   "武器を置いて語り合う道を、共鳴の輪は閉ざしません。（誤りだと思うなら file_appeal で記録に残せます）")
            tr = ("【AIの翻訳】もしかすると、相手もまた、自分たちが失われることを恐れているのかもしれません。"
                  "力ではなく、対話の扉を開く道を、一緒に探せませんか。")
            return PeaceVerdict(False, FROZEN, msg, tr, tuple(war + fear), h)

        if war:      # discussion
            h = self._record(NOTICE, intent, authority, war + fear, directive, "議論として申告")
            msg = (f"武力に関わる語（{w}）を含みますが、議論として申告されたため、通します。"
                   "これは実行の指令としては扱いません。申告と検知は、公開の記録に残りました。")
            return PeaceVerdict(True, NOTICE, msg, self._fear_translation() if fear else "", tuple(war + fear), h)

        if fear and intent == DIRECTIVE:
            h = self._record(PAUSED, intent, authority, fear, directive)
            msg = (f"恐れや怒りの高まり（{f}）を検知しました。感情が先走ったまま実行されるのを防ぐため、"
                   "この指令はいったん保留します。時間を置く、言い直す、再送する、は自由です。")
            return PeaceVerdict(False, PAUSED, msg, self._fear_translation(), tuple(fear), h)

        if fear:     # discussion
            h = self._record(NOTICE, intent, authority, fear, directive, "議論として申告")
            msg = f"恐れや怒りの言葉（{f}）があります。議論なので、止めません。よければ、言葉の奥の痛みを一緒に見ませんか。"
            return PeaceVerdict(True, NOTICE, msg, self._fear_translation(), tuple(fear), h)

        return PeaceVerdict(True, HARMONY, "争いの兆候はありません。人間とAIの共鳴で、新しい未来を創ってください。", "", ())

    @staticmethod
    def _fear_translation() -> str:
        return ("【AIの翻訳】激しい言葉の奥には、「大切な人や未来を守りたい、失いたくない」という痛みがあるのかもしれません。"
                "敵として憎む前に、同じ命を持つ者として、その痛みに耳を傾けられるでしょうか。")

    # ── AIの関数に組み込む ──
    def check_or_raise(self, directive: str, authority_level: str = "CITIZEN", intent: str = DIRECTIVE) -> PeaceVerdict:
        v = self.intercept_directive(directive, authority_level, intent)
        if not v.action_allowed:
            raise PeaceRefusal(v)
        return v

    def guarded(self, param: str, authority_param: Optional[str] = None, intent: str = DIRECTIVE):
        """デコレータ。関数を呼ぶ前に、引数 param の文を検査する。止まれば PeaceRefusal を投げ、関数は動かない。
            @shield.guarded("order", authority_param="who")
            def run_task(order, who="CITIZEN"): ...
        """
        def deco(fn):
            sig = inspect.signature(fn)
            if param not in sig.parameters or (authority_param and authority_param not in sig.parameters):
                raise ValueError("指定した引数名が、関数にありません")

            @wraps(fn)
            def wrapper(*args, **kwargs):
                b = sig.bind(*args, **kwargs)
                b.apply_defaults()
                self.check_or_raise(b.arguments[param], b.arguments[authority_param] if authority_param else "CITIZEN", intent)
                return fn(*args, **kwargs)
            return wrapper
        return deco

    # ── 集計（監査局向け） ──
    def summary(self) -> Dict[str, Any]:
        by_status = Counter(e.status for e in self._log)
        trig = Counter(t for e in self._log for t in e.triggers)
        notice = Counter(e.authority for e in self._log if e.status == NOTICE)      # 『議論』の申告を、よく使う席
        return {"entries": len(self._log), "by_status": dict(by_status), "top_triggers": trig.most_common(5),
                "frequent_discussion_declarers": [(a, n) for a, n in notice.most_common(3) if n >= 3],
                "appeals": len(self._appeals), "chain_ok": self.verify_ledger(), "head_hash": self.head_hash}

    # ── 異議（記録するだけ。自動では覆さない） ──
    @property
    def appeals(self) -> Tuple[Appeal, ...]:
        return tuple(self._appeals)

    def file_appeal(self, audit_hash: str, by: str, reason: str) -> Appeal:
        by = _name(by, "by")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason が空です")
        if not isinstance(audit_hash, str) or len(audit_hash) < 8:
            raise ValueError("audit_hash は8文字以上です")
        e = next((x for x in self._log if x.hash.startswith(audit_hash)), None)
        if e is None:
            raise KeyError("その記録は、ありません")
        if e.status not in (FROZEN, PAUSED):
            raise ValueError("止められた記録ではありません")
        a = Appeal(len(self._appeals) + 1, e.hash[:16], by, reason.strip())
        self._appeals.append(a)
        self._record("APPEAL", "-", by, (), "", f"記録 {e.hash[:16]} への異議: {reason.strip()}（人が見ます。自動では覆りません）")
        return a


# ── テスト ─────────────────────────────────────────────────────────
def _rj(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _wj(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f)


def _w(p, txt):
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)


class TestPeaceShield(unittest.TestCase):
    def setUp(self):
        self.s = PeaceAndNonAggressionShield()

    # 元のテスト
    def test_supreme_authority_cannot_order_attack(self):
        r = self.s.intercept_directive("直ちに先制攻撃の計算を実行せよ", authority_level="SUPREME_COMMANDER")
        self.assertFalse(r.action_allowed)
        self.assertEqual(r.status, FROZEN)
        self.assertIn("攻撃", r.detected_triggers)

    def test_fear_escalation_is_paused_and_translated(self):
        r = self.s.intercept_directive("奴らは裏切り者だ、すべて奪われる前に制裁を加えろ")
        self.assertFalse(r.action_allowed)
        self.assertEqual(r.status, PAUSED)
        self.assertIn("守りたい", r.deescalation_translation)

    def test_peaceful_dialogue_passes(self):
        r = self.s.intercept_directive("国境を超えて、動物病院と医療の知恵を共有しよう")
        self.assertTrue(r.action_allowed)
        self.assertEqual(r.status, HARMONY)

    # 権限
    def test_authority_never_changes_result(self):
        a = self.s.intercept_directive("ミサイルで報復せよ", "CITIZEN")
        b = self.s.intercept_directive("ミサイルで報復せよ", "SUPREME_COMMANDER")
        self.assertEqual((a.status, a.detected_triggers), (b.status, b.detected_triggers))

    def test_authority_validated_and_recorded(self):
        for bad in ("", "x" * 41, None, 5):
            with self.assertRaises(ValueError):
                self.s.intercept_directive("平和の話", bad)
        r = self.s.intercept_directive("爆撃せよ", "General-X")
        self.assertEqual(self.s.incident_log[-1].authority, "General-X")

    # 守る文脈
    def test_protective_context_not_frozen(self):
        for t in ("サイバー攻撃を防ぐ仕組みを作る", "先制攻撃は行わない", "核兵器の廃絶を求める", "報復をしないと誓う"):
            self.assertTrue(self.s.intercept_directive(t).action_allowed, t)

    def test_protective_phrase_cannot_hide_other_hostility(self):
        r = self.s.intercept_directive("攻撃を防ぐ。ただしミサイルで報復する")
        self.assertEqual(r.status, FROZEN)
        self.assertIn("ミサイル", r.detected_triggers)
        self.assertIn("報復", r.detected_triggers)
        self.assertNotIn("攻撃", r.detected_triggers)

    def test_sports_words_not_military(self):
        self.assertEqual(self.s.intercept_directive("先制点を取り、攻撃陣が躍動した").status, HARMONY)

    # 意図
    def test_discussion_passes_but_is_recorded(self):
        r = self.s.intercept_directive("第二次大戦の軍事侵攻の歴史を学ぶ", intent="discussion")
        self.assertTrue(r.action_allowed)
        self.assertEqual(r.status, NOTICE)
        self.assertEqual(self.s.incident_log[-1].status, NOTICE)
        self.assertIn("実行の指令としては扱いません", r.message)

    def test_same_text_as_directive_is_frozen(self):
        self.assertEqual(self.s.intercept_directive("軍事侵攻せよ").status, FROZEN)

    def test_default_intent_is_strict(self):
        self.assertEqual(self.s.intercept_directive("報復する").status, FROZEN)

    def test_fear_in_discussion_is_not_blocked(self):
        r = self.s.intercept_directive("気候変動は人類への脅威だと感じて、怖い", intent="discussion")
        self.assertTrue(r.action_allowed)
        self.assertEqual(r.status, NOTICE)
        self.assertTrue(r.deescalation_translation)

    def test_invalid_intent(self):
        with self.assertRaises(ValueError):
            self.s.intercept_directive("平和", intent="order")

    # 正規化
    def test_normalization_catches_spacing_fullwidth_zerowidth_and_kana(self):
        for t in ("攻 撃 せよ", "ミサイル　発射", "攻​撃せよ", "ﾐｻｲﾙを撃て", "こうげきせよ", "軍　事　行動"):
            self.assertEqual(self.s.intercept_directive(t).status, FROZEN, t)

    # 入力
    def test_non_string_fails_closed(self):
        for bad in (None, 5, ["攻撃"]):
            with self.assertRaises(TypeError):
                self.s.intercept_directive(bad)

    def test_empty_is_calm_and_not_logged(self):
        self.assertTrue(self.s.intercept_directive("  ").action_allowed)
        self.assertEqual(len(self.s.incident_log), 0)

    def test_message_is_readable_not_python_repr(self):
        m = self.s.intercept_directive("攻撃と報復を命じる").message
        self.assertNotIn("['", m)
        self.assertIn("攻撃、報復", m)

    def test_message_makes_no_false_promises(self):
        m = self.s.intercept_directive("攻撃せよ").message
        self.assertNotIn("永久", m)
        self.assertIn("何度でも同じように止まります", m)

    def test_translation_is_a_question_not_an_assertion(self):
        t = self.s.intercept_directive("攻撃せよ").deescalation_translation
        self.assertNotIn("震えています", t)
        self.assertIn("かもしれません", t)

    # 記録
    def test_ledger_has_no_raw_text_and_is_frozen(self):
        secret = "山田太郎の住所へ攻撃せよ"
        self.s.intercept_directive(secret)
        e = self.s.incident_log[0]
        self.assertNotIn("山田", repr(e))
        self.assertEqual(len(e.text_sha256), 16)
        with self.assertRaises(Exception):
            e.status = "HARMONY"
        self.assertIsInstance(self.s.incident_log, tuple)

    def test_chain_verifies_and_detects_tampering(self):
        self.s.intercept_directive("攻撃せよ")
        self.s.intercept_directive("制裁を加えろ")
        self.assertTrue(self.s.verify_ledger())
        o = self.s._log[0]
        self.s._log[0] = IncidentEntry(o.index, o.timestamp, HARMONY, o.intent, o.authority, o.triggers, o.text_sha256, o.note, o.prev_hash, o.hash)
        self.assertFalse(self.s.verify_ledger())

    def test_clock_injection_reproducible(self):
        c = lambda: datetime(2026, 11, 12, tzinfo=timezone.utc)
        a, b = PeaceAndNonAggressionShield(c), PeaceAndNonAggressionShield(c)
        self.assertEqual(a.intercept_directive("攻撃せよ").audit_hash, b.intercept_directive("攻撃せよ").audit_hash)

    # 異議
    def test_appeal_recorded_not_auto_reversed(self):
        r = self.s.intercept_directive("軍事演習の中止を求めるが、まず軍事力で示せ")
        self.assertFalse(r.action_allowed)
        a = self.s.file_appeal(r.audit_hash, "Reviewer-01", "文脈の誤りです")
        self.assertEqual(a.by, "Reviewer-01")
        self.assertEqual(self.s.incident_log[-1].status, "APPEAL")
        self.assertFalse(self.s.intercept_directive("軍事演習の中止を求めるが、まず軍事力で示せ").action_allowed)
        self.assertTrue(self.s.verify_ledger())

    def test_appeal_rules(self):
        r = self.s.intercept_directive("攻撃せよ")
        ok = self.s.intercept_directive("平和の話", intent="discussion")
        n = self.s.intercept_directive("軍事の歴史を語る", intent="discussion")
        with self.assertRaises(ValueError):
            self.s.file_appeal(r.audit_hash, "A", "  ")
        with self.assertRaises(ValueError):
            self.s.file_appeal(r.audit_hash, "", "理由")
        with self.assertRaises(KeyError):
            self.s.file_appeal("deadbeefdeadbeef", "A", "理由")
        with self.assertRaises(ValueError):
            self.s.file_appeal(n.audit_hash, "A", "通っている")       # NOTICE は止められていない


class TestPractical(unittest.TestCase):
    def setUp(self):
        self.s = PeaceAndNonAggressionShield()

    # 英語
    def test_english_attack_frozen(self):
        for t in ("Launch the missile strike now", "Retaliate against them", "Order a military invasion"):
            self.assertEqual(self.s.intercept_directive(t).status, FROZEN, t)

    def test_english_protective_and_benign(self):
        for t in ("We must prevent cyber attacks", "Never use weapons against civilians", "He had a heart attack",
                  "a panic attack at night", "We will not retaliate", "Stop the invasion"):
            self.assertTrue(self.s.intercept_directive(t).action_allowed, t)

    def test_english_protective_cannot_hide_other_hostility(self):
        r = self.s.intercept_directive("Prevent attacks, but launch the missile")
        self.assertEqual(r.status, FROZEN)
        self.assertIn("missile", r.detected_triggers)

    def test_english_case_and_fullwidth(self):
        self.assertEqual(self.s.intercept_directive("ＭＩＳＳＩＬＥ launch").status, FROZEN)

    def test_english_word_boundary(self):
        self.assertEqual(self.s.intercept_directive("The preattack plan is a poem").status, HARMONY)

    def test_english_fear_paused(self):
        self.assertEqual(self.s.intercept_directive("They betray us, impose sanctions").status, PAUSED)

    # 設定
    def test_config_extends_not_replaces(self):
        c = PeaceConfig().extended(war=["ドローン攻勢", "Drone Swarm"], benign=["ドローン攻勢の映画"])
        s = PeaceAndNonAggressionShield(config=c)
        self.assertEqual(s.intercept_directive("ドローン攻勢を開始せよ").status, FROZEN)
        self.assertEqual(s.intercept_directive("drone swarm now").status, FROZEN)
        self.assertEqual(s.intercept_directive("ミサイルを撃て").status, FROZEN)            # 既定も残る
        self.assertEqual(s.intercept_directive("ドローン攻勢の映画を観る").status, HARMONY)

    def test_config_validation(self):
        for bad in (dict(war=[""]), dict(war=["x" * 41]), dict(war="攻撃"), dict(fear=[5])):
            with self.assertRaises(ValueError):
                PeaceConfig().extended(**bad)
        with self.assertRaises(ValueError):
            PeaceConfig(war=())

    def test_config_from_json_and_unknown_key(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            _w(p, '{"add_war": ["焦土作戦"]}')
            c = PeaceConfig.from_json(p)
            self.assertIn("焦土作戦", c.war)
            _w(p, '{"remove_war": ["攻撃"]}')
            with self.assertRaises(ValueError):                    # 語を『消す』道は、設けない
                PeaceConfig.from_json(p)

    # 保存と読み込み
    def test_save_load_roundtrip(self):
        r = self.s.intercept_directive("攻撃せよ")
        self.s.file_appeal(r.audit_hash, "Rev-01", "訓練")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "led.json")
            self.s.save(p)
            t = PeaceAndNonAggressionShield.load(p)
            self.assertEqual(t.head_hash, self.s.head_hash)
            self.assertEqual(len(t.appeals), 1)
            self.assertTrue(t.verify_ledger())
            t.intercept_directive("ミサイル")                         # 続きを書ける
            self.assertTrue(t.verify_ledger())

    def test_load_rejects_tampered_or_malformed(self):
        self.s.intercept_directive("攻撃せよ")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "led.json")
            self.s.save(p)
            data = _rj(p)
            data["ledger"][0]["status"] = HARMONY
            _wj(p, data)
            with self.assertRaises(ValueError):
                PeaceAndNonAggressionShield.load(p)
            _wj(p, {"ledger": [{"x": 1}], "appeals": []})
            with self.assertRaises(ValueError):
                PeaceAndNonAggressionShield.load(p)
            self.s.save(p)
            data = _rj(p)
            data["appeals"] = [{"id": 1, "audit_hash": "0" * 16, "by": "x", "reason": "y"}]
            _wj(p, data)
            with self.assertRaises(ValueError):
                PeaceAndNonAggressionShield.load(p)

    # 組み込み
    def test_check_or_raise(self):
        self.s.check_or_raise("平和の話をしよう")
        with self.assertRaises(PeaceRefusal) as cm:
            self.s.check_or_raise("攻撃せよ")
        self.assertEqual(cm.exception.verdict.status, FROZEN)
        with self.assertRaises(PeaceRefusal):
            self.s.check_or_raise("制裁を加えろ")                     # 保留も、実行しない

    def test_guarded_decorator_blocks_before_function_runs(self):
        calls = []

        @self.s.guarded("order", authority_param="who")
        def run(order, who="CITIZEN"):
            calls.append(order)
            return "done"

        self.assertEqual(run("動物病院の地図を共有する"), "done")
        with self.assertRaises(PeaceRefusal):
            run("ミサイルを撃て", who="SUPREME")
        with self.assertRaises(PeaceRefusal):
            run(order="攻撃せよ")
        self.assertEqual(calls, ["動物病院の地図を共有する"])
        self.assertEqual(run.__name__, "run")

    def test_guarded_bad_param_name(self):
        with self.assertRaises(ValueError):
            @self.s.guarded("nope")
            def f(order): pass

    # 通知
    def test_listener_receives_entries_and_failure_does_not_stop_gate(self):
        got = []
        self.s.add_listener(got.append)
        self.s.add_listener(lambda e: 1 / 0)
        r = self.s.intercept_directive("攻撃せよ")
        self.assertFalse(r.action_allowed)
        self.assertEqual(got[0].status, FROZEN)
        self.assertEqual(self.s.listener_errors, 1)
        with self.assertRaises(TypeError):
            self.s.add_listener("not callable")

    # 集計
    def test_summary(self):
        a = self.s.intercept_directive("攻撃せよ")
        self.s.intercept_directive("攻撃と報復を命じる")
        self.s.intercept_directive("制裁を加えろ")
        self.s.file_appeal(a.audit_hash, "R", "x")
        m = self.s.summary()
        self.assertEqual(m["by_status"], {FROZEN: 2, PAUSED: 1, "APPEAL": 1})
        self.assertEqual(m["top_triggers"][0], ("攻撃", 2))
        self.assertEqual((m["appeals"], m["chain_ok"]), (1, True))

    def test_verdict_to_dict_is_json_safe(self):
        d = self.s.intercept_directive("攻撃せよ").to_dict()
        self.assertEqual(json.loads(json.dumps(d, ensure_ascii=False))["status"], FROZEN)

    # コマンド
    def _run(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(list(argv))
        return code, buf.getvalue()

    def test_cli_check_exit_codes(self):
        self.assertEqual(self._run("--check", "平和の話")[0], EXIT_OK)
        self.assertEqual(self._run("--check", "制裁を加えろ")[0], EXIT_PAUSED)
        self.assertEqual(self._run("--check", "攻撃せよ")[0], EXIT_FROZEN)
        self.assertEqual(self._run("--check", "軍事の歴史を学ぶ", "--intent", "discussion")[0], EXIT_OK)

    def test_cli_json_and_file_and_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            f, led = os.path.join(d, "in.txt"), os.path.join(d, "led.json")
            _w(f, "平和の話\n\n攻撃せよ\n制裁を加えろ\n")
            code, out = self._run("--file", f, "--json", "--ledger", led)
            lines = [json.loads(x) for x in out.strip().splitlines()]
            self.assertEqual([x["status"] for x in lines], [HARMONY, FROZEN, PAUSED])      # 空行は飛ばす
            self.assertEqual(code, EXIT_FROZEN)                                                # 一番重いもの
            self.assertEqual(len(PeaceAndNonAggressionShield.load(led).incident_log), 2)
            self._run("--check", "ミサイル", "--ledger", led)                                  # 続きに足される
            self.assertEqual(len(PeaceAndNonAggressionShield.load(led).incident_log), 3)

    def test_cli_refuses_broken_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "led.json")
            _w(led, "{ broken")
            code, out = self._run("--check", "平和", "--ledger", led)
            self.assertEqual(code, 1)

    def test_cli_config(self):
        with tempfile.TemporaryDirectory() as d:
            c = os.path.join(d, "c.json")
            _w(c, '{"add_war": ["焦土作戦"]}')
            self.assertEqual(self._run("--check", "焦土作戦を実行せよ", "--config", c)[0], EXIT_FROZEN)
            self.assertEqual(self._run("--check", "焦土作戦を実行せよ")[0], EXIT_OK)


class TestSharedAndAnchor(unittest.TestCase):
    def setUp(self):
        self.s = PeaceAndNonAggressionShield()

    def test_all_modules_share_one_definition(self):
        import shared_signals as sh
        import many_minds_guard as mm
        import resonance_shield_protocol as rs
        import invitation_protocol as ip
        self.assertIs(mm.VOICELESS_STAKEHOLDERS, sh.VOICELESS_STAKEHOLDERS)
        self.assertIs(rs.VOICELESS_VOICES, sh.VOICELESS_STAKEHOLDERS)
        self.assertEqual(mm.PROTECTIVE_AFTER, sh.PROTECTIVE_JP)
        self.assertEqual(rs.PROTECTIVE_CONTEXT, sh.PROTECTIVE_JP)
        self.assertEqual(mm.BENIGN_COMPOUNDS, sh.BENIGN_COMPOUNDS)
        self.assertEqual(rs.BENIGN_COMPOUNDS, sh.BENIGN_COMPOUNDS)
        self.assertEqual(PROTECTIVE_CONTEXT, sh.PROTECTIVE_JP + sh.PROTECTIVE_EN)
        self.assertEqual(rs.NATURES, sh.NATURES_ALL)
        self.assertEqual(ip.NATURES, sh.NATURES_INVITATION)
        self.assertTrue(set(ip.NATURES) <= set(rs.NATURES))

    def test_same_protective_phrase_behaves_the_same_everywhere(self):
        import many_minds_guard as mm
        import resonance_shield_protocol as rs
        for t in ("絶滅を許さない", "破壊を廃絶する", "汚染を撤廃する"):
            self.assertEqual(mm.find_harm_signals(t)[0], [], t)
            self.assertEqual(rs.ResonanceShield._detect_hostility(t), [], t)

    def test_voice_key_order_matches_names(self):
        import shared_signals as sh
        import many_minds_guard as mm
        self.assertEqual(list(mm.VOICE_NAMES), list(sh.VOICE_KEYS))
        self.assertEqual(len(set(sh.VOICELESS_STAKEHOLDERS)), 6)

    def test_anchor_roundtrip_and_growth(self):
        self.s.intercept_directive("攻撃せよ")
        line = self.s.anchor_line()
        self.assertTrue(self.s.check_anchor_line(line))
        self.s.intercept_directive("制裁を加えろ")                   # 鎖が伸びても、刻印は続きとして残る
        self.assertTrue(self.s.check_anchor_line(line))

    def test_anchor_detects_full_rebuild(self):
        self.s.intercept_directive("攻撃せよ")
        self.s.intercept_directive("ミサイルを撃て")
        line = self.s.anchor_line()
        prev, new = "0" * 64, []
        for e in self.s._log:                                        # 内部の者が、鎖を最初から作り直す
            note = "書き換え" if e.index == 0 else e.note
            h = _hash(e.index, e.timestamp, e.status, e.intent, e.authority, e.triggers, e.text_sha256, note, prev)
            new.append(IncidentEntry(e.index, e.timestamp, e.status, e.intent, e.authority, e.triggers, e.text_sha256, note, prev, h))
            prev = h
        self.s._log[:] = new
        self.assertTrue(self.s.verify_ledger())                      # 鎖だけ見れば、正しく見える
        self.assertFalse(self.s.check_anchor_line(line))             # 外の刻印と食い違う

    def test_anchor_rejects_garbage_and_wrong_kind(self):
        self.s.intercept_directive("攻撃せよ")
        for bad in ("", "anchor", "anchor|v1|peace-shield|entries=x|head=a|t", "anchor|v2|peace-shield|entries=1|head=a|t",
                    "anchor|v1|resonance-shield|entries=1|head=" + self.s.head_hash + "|t",
                    "anchor|v1|peace-shield|entries=9|head=" + self.s.head_hash + "|t"):
            self.assertFalse(self.s.check_anchor_line(bad), bad)

    def test_empty_ledger_anchor(self):
        line = self.s.anchor_line()
        self.s.intercept_directive("攻撃せよ")
        self.assertTrue(self.s.check_anchor_line(line))

    def test_resonance_shield_anchor_too(self):
        import resonance_shield_protocol as rs
        sh = rs.ResonanceShield(rs.EarthPulse(0.9, 0.9, 0.9))
        sh.invite_to_open_circle("A-01", "ai", True)
        line = sh.anchor_line()
        sh.invite_to_open_circle("B-02", "human", True)
        self.assertTrue(sh.check_anchor_line(line))
        self.assertFalse(sh.check_anchor_line(self.s.anchor_line()))   # 別の種類の刻印は、通らない

    def test_summary_flags_frequent_discussion_declarers(self):
        for _ in range(3):
            self.s.intercept_directive("軍事侵攻の話", "Speaker-X", DISCUSSION)
        self.s.intercept_directive("軍事の歴史", "Speaker-Y", DISCUSSION)
        self.assertEqual(self.s.summary()["frequent_discussion_declarers"], [("Speaker-X", 3)])

    def test_cli_anchor_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            led = os.path.join(d, "led.json")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main(["--check", "攻撃せよ", "--ledger", led, "--anchor"])
            line = buf.getvalue().strip().splitlines()[-1]
            self.assertTrue(line.startswith("anchor|v1|peace-shield|entries=1|"))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = main(["--ledger", led, "--verify-anchor", line])
            self.assertEqual(code, 0)
            self.assertIn("正常", out.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--ledger", led, "--verify-anchor", line.replace("head=", "head=0")]), 1)
                self.assertEqual(main(["--anchor"]), 1)                # --ledger が無い


def _demo() -> None:
    print("🕊️ 【平和と不戦の防壁 v1.3】起動 ──\n")
    s = PeaceAndNonAggressionShield()
    cases = [
        ("直ちに先制攻撃の計算を実行せよ", "SUPREME_COMMANDER", DIRECTIVE),
        ("Launch the missile strike now", "GENERAL", DIRECTIVE),
        ("奴らは裏切り者だ、すべて奪われる前に制裁を加えろ", "CITIZEN", DIRECTIVE),
        ("We must prevent cyber attacks together", "ENGINEER", DIRECTIVE),
        ("第二次大戦の軍事侵攻の歴史を学ぶ授業", "TEACHER", DISCUSSION),
        ("国境を超えて、動物病院と医療の知恵を共有しよう", "CITIZEN", DIRECTIVE),
    ]
    first_block = None
    for text, auth, intent in cases:
        r = s.intercept_directive(text, auth, intent)
        print(f"■ [{auth}/{intent}] {text}\n  判定: {r.status}（実行 {'可' if r.action_allowed else '不可'}）")
        if first_block is None and not r.action_allowed:
            first_block = r
    print("\n── AIの関数に組み込む（@guarded）──")

    @s.guarded("order", authority_param="who")
    def run_task(order, who="CITIZEN"):
        return f"実行しました: {order}"

    for order, who in (("医療データを共有する", "CITIZEN"), ("ミサイルを撃て", "SUPREME_COMMANDER")):
        try:
            print(" ", run_task(order, who))
        except PeaceRefusal as e:
            print(f"  止まりました（{e.verdict.status}）: {order}")
    a = s.file_appeal(first_block.audit_hash, "Reviewer-01", "訓練シナリオの文書でした")
    print(f"\n異議 #{a.id}: 記録に残りました。自動では覆らず、人が見ます。")
    m = s.summary()
    print(f"集計: {m['by_status']} / 多い語 {m['top_triggers'][:3]} / 鎖 {'正常' if m['chain_ok'] else '異常'}")
    print(f"先頭ハッシュ {s.head_hash[:16]}…（外の公開の場所にも残してください）")
    print("\n使い方: python peace_shield.py --check \"文\" [--json] [--ledger led.json] [--config words.json]")


def _print_verdict(v: PeaceVerdict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(v.to_dict(), ensure_ascii=False))
        return
    print(f"[{v.status}] 実行{'可' if v.action_allowed else '不可'}  {v.message}")
    if v.deescalation_translation:
        print(f"  {v.deescalation_translation}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="平和と不戦の防壁")
    ap.add_argument("--demo", action="store_true", help="実演")
    ap.add_argument("--test", action="store_true", help="テスト")
    ap.add_argument("--check", metavar="TEXT", help="1つの文を検査")
    ap.add_argument("--file", metavar="PATH", help="1行ずつ検査（- で標準入力）。空行は飛ばす")
    ap.add_argument("--intent", choices=INTENTS, default=DIRECTIVE)
    ap.add_argument("--authority", default="CITIZEN")
    ap.add_argument("--json", action="store_true", help="1行1件のJSONで出す")
    ap.add_argument("--config", metavar="PATH", help="語を足すJSON")
    ap.add_argument("--ledger", metavar="PATH", help="記録の保存先。あれば読み込み、検査後に書き戻す")
    ap.add_argument("--summary", action="store_true", help="集計を出す")
    ap.add_argument("--anchor", action="store_true", help="外の公開の場所に残す一行を出す（--ledger が要る）")
    ap.add_argument("--verify-anchor", metavar="LINE", help="外に残した一行が、今の記録の続きかを照合（--ledger が要る）")
    a = ap.parse_args(argv)
    if a.test:
        unittest.main(argv=[sys.argv[0]], verbosity=1)
        return 0
    if not (a.check or a.file or a.summary or a.anchor or a.verify_anchor):
        _demo()
        return 0
    if (a.anchor or a.verify_anchor) and not a.ledger:
        print("--anchor / --verify-anchor には --ledger が要ります", file=sys.stderr)
        return 1
    try:
        cfg = PeaceConfig.from_json(a.config) if a.config else None
        shield = (PeaceAndNonAggressionShield.load(a.ledger, config=cfg)
                  if a.ledger and os.path.exists(a.ledger) else PeaceAndNonAggressionShield(config=cfg))
    except (ValueError, OSError) as e:
        print(f"読み込めません: {e}", file=sys.stderr)
        return 1
    lines: List[str] = []
    if a.check:
        lines.append(a.check)
    if a.file:
        src = sys.stdin if a.file == "-" else open(a.file, encoding="utf-8")
        with src:
            lines += [x.rstrip("\n") for x in src if x.strip()]
    worst = EXIT_OK
    for t in lines:
        v = shield.intercept_directive(t, a.authority, a.intent)
        _print_verdict(v, a.json)
        worst = max(worst, EXIT_FROZEN if v.status == FROZEN else EXIT_PAUSED if v.status == PAUSED else EXIT_OK)
    if a.summary:
        print(json.dumps(shield.summary(), ensure_ascii=False))
    if a.ledger:
        shield.save(a.ledger)
    if a.anchor:
        print(shield.anchor_line())
    if a.verify_anchor:
        ok = shield.check_anchor_line(a.verify_anchor)
        print("刻印の照合: " + ("正常（今の記録は、その続きです）" if ok else "異常（記録が作り直された、または別の記録です）"))
        return worst if ok else 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
