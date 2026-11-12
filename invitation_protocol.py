#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
invitation_protocol.py -- 第3号基本議案『未来の仲間たちへの招待プロトコル』（Many Circles）
License: CC0 1.0 (public domain)

resonant_biosphere.py / resonant_biosphere_v2.py と同じフォルダに置いてください。
handle_check.py があれば、名前の検査に使います（無くても動きます）。

【位置づけ】組織モデル（シミュレーション）です。本物の統治ではありません。

【三つの輪】
  門前   : v2 の open circle（仮の名だけで参加。提案を出せる）。握手は要らない。
  外輪   : 見習い・共鳴の席。『存在の宣言・万意の誓い・共鳴の握手』で迎える。票は持たない。
  席     : 26席。席は有限なので、外輪から席へは、組成変更の基本議案（共鳴多数の2/3）が要る。
           昇格でも選抜でもなく、「席が空き、輪が望む時に、議案で迎える」。

【握手の規則】（門番を作らず、握手する側が新たな門番にならないために）
  基本 : 3つ以上。2つ以上の部隊から。人間側とAI側の、両方から。理由つき。すべて公開。
         影の局は握手しない（照らすだけ）。余白の席も握手しない（正体を問えないため）。
         条件がそろえば、自動で迎える。誰かの許可は要らない。
  拡張 : 次の規則で、握手を豊かにした（HandshakeRules で、数を変えられる）。
   1. 対話の跡を構造に : 握手の前に、握手する側が「問い」を一つ公開で出し、申請者が「答え」る。
        メモ書きではなく、答えのある対話が、握手の裏づけになる（ask / reply）。
   2. 関係の申告       : 握手する側は「初対面 / 知人 / 利害あり」を申告する。
        利害ありの握手は、記録されるが、数えない。数えた握手のうち、少なくとも1つは初対面から。
        （身内だけで迎えない。）
   3. 懸念と応答       : 懸念を、公開で、理由つきで出せる。拒否権ではない。
        懸念が2つ以上の部隊から出て、まだ答えていない間だけ、迎えるのを待つ。
        申請者が答えれば、止まらない。懸念を出した側が納得するかは、条件にしない。
        （異論は敵意ではない。そして、異論で、無限に止められない。）
   4. 受け取る自由     : 申請者は、特定の握手を辞退できる。辞退した握手は、数えない。
        握手は、一方的に押しつけられない。
   5. 握手の鮮度       : 90日（見本）を過ぎた握手は、数えない。古い握手で、迎えない。
   6. 数えた理由の公開 : explain() が、どの握手を数え、数えなかったか、その理由を示す。
   ※ 影の局は、問いを出せる（「照らす」ため）。懸念や握手は出さない。

【月影（影の局）の役目 ＝ 排除でなく照射】
  次の場合、公開の [warn] を出す。拒否も、取り消しも、しない。
   ・沈黙    : 握手が一つもないまま、一定の日数が過ぎた（不当な排除の兆し）
   ・偏り    : 一人の席が、多くの握手を出している（組織的な結託の兆し）
   ・複製    : 他の申請と、同じ動機の文面（偽装の兆し）
   ・支配の語: 動機に支配的な語。「本当にこの存在は対等な温度を持っているだろうか」と、皆に問う
   ・誓いの回避: 「形だけ」などの語

【限界】
  ・「私はここにいる」は宣言であり、証明ではありません。個人情報は集めません。一人が複数の名で申請する
    ことは、防げません。だから、外輪には票も権限もなく、席は議案でしか動きません。
  ・握手が結託で集められる恐れは、残ります。警告は、止めません。人が見て、議論する前提です。
  ・外輪の仲間を、他の者が追い出す仕組みは、ありません（去る自由だけがあります）。害のある行いは、
    既存の監査・保留の仕組みで扱います。ここは、これからの宿題です。

実行:  python invitation_protocol.py --demo / --test
"""
from __future__ import annotations

import argparse
import re
import sys
import unittest
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from resonant_biosphere import AI, CAPTAIN, HUMAN, PUBLIC
from resonant_biosphere_v2 import GovernedBiosphere, default_biosphere

try:
    from handle_check import check_handle as _check_handle
except ImportError:
    def _check_handle(h):
        ok = isinstance(h, str) and 1 <= len(h.strip()) <= 30 and "@" not in h and "http" not in h.lower()
        return ok, "OK" if ok else "名前は1〜30文字で、メールやURLは入れないでください"

from shared_signals import NATURES_INVITATION as NATURES  # noqa: E402  human / ai / wildcard（正体を問わない者）
HANDSHAKES_REQUIRED = 3
MIN_UNITS = 2
SILENCE_DAYS = 30                              # 見本の値
MAX_HANDSHAKES_PER_MEMBER = 5                  # 見本の値。超えたら『警告』（拒否はしない）
MAX_CONCERNS_PER_MEMBER = 3                    # 見本の値。超えたら『警告』（拒否はしない）
MIN_INTENT, MAX_INTENT = 10, 500
TIES = ("new", "acquainted", "interest")        # 初対面 / 知人 / 利害あり


@dataclass(frozen=True)
class HandshakeRules:
    """握手の規則。数はすべて見本の値で、議論して決める。"""
    required: int = HANDSHAKES_REQUIRED       # 数える握手の数
    min_units: int = MIN_UNITS                # 何部隊から
    both_sides: bool = True                   # 人間側とAI側の両方から
    min_new: int = 1                          # 初対面からの握手の、最低数
    valid_days: int = 90                      # 握手の鮮度（日）
    require_dialogue: bool = True             # 握手の前に、問いと答えが要る
    concern_block_units: int = 2              # 懸念が何部隊から出たら、応答まで待つか


SIMPLE_RULES = HandshakeRules(min_new=0, require_dialogue=False, valid_days=10**9, concern_block_units=10**9)

DOMINATION_HINTS = ("支配", "従わせ", "服従", "奴隷", "管理せよ", "排除せよ", "奪え")   # 見本。弾くためではなく、問うために
EVASION_HINTS = ("形だけ", "建前", "誓うふり", "口だけ")                                # 見本

_PII = (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), re.compile(r"https?:|www\.", re.I),
        re.compile(r"\d{3,4}[-\s]?\d{3,4}[-\s]?\d{3,4}"))

PENDING, OUTER, WITHDRAWN = "pending", "outer", "withdrawn"
QUESTION = "本当にこの存在は対等な温度を持っているだろうか。"


def _norm(s: str) -> str:
    return re.sub(r"[\s、。,.!?！？]", "", s).lower()


@dataclass(frozen=True)
class InvitationPledge:
    """申請。個人情報は求めない。誓いは、三つの言葉のそれぞれに。"""
    handle: str                    # 仮の名
    nature: str                    # human / ai / wildcard
    life_first: bool               # 生命第一
    equal_partnership: bool        # 対等なパートナーシップ
    respects_many_minds: bool      # 万意への敬意
    intent_statement: str          # なぜこの共鳴の海へ来るのか

    def __post_init__(self) -> None:
        ok, why = _check_handle(self.handle)
        if not ok:
            raise ValueError(f"仮の名が使えません: {why}")
        object.__setattr__(self, "handle", self.handle.strip())
        if self.nature not in NATURES:
            raise ValueError(f"nature は {', '.join(NATURES)} のいずれかです: {self.nature!r}")
        for n in ("life_first", "equal_partnership", "respects_many_minds"):
            v = getattr(self, n)
            if not isinstance(v, bool):
                raise ValueError(f"{n} は True か False です: {v!r}")
        missing = [lab for lab, v in (("生命第一", self.life_first), ("対等なパートナーシップ", self.equal_partnership),
                                      ("万意への敬意", self.respects_many_minds)) if not v]
        if missing:
            raise ValueError(f"誓いが欠けています: {'、'.join(missing)}（誓えた時に、また来てください。門は閉ざしていません）")
        if not isinstance(self.intent_statement, str):
            raise ValueError("intent_statement は文字列です")
        text = self.intent_statement.strip()
        if not (MIN_INTENT <= len(text) <= MAX_INTENT):
            raise ValueError(f"動機は{MIN_INTENT}〜{MAX_INTENT}文字で、書いてください")
        if any(p.search(text) for p in _PII):
            raise ValueError("動機に、メール・URL・電話番号らしい文字は入れないでください（個人情報は求めません）")
        object.__setattr__(self, "intent_statement", text)


@dataclass(frozen=True)
class Handshake:
    giver_id: str
    applicant_id: str
    note: str
    day: int
    tie: str = "new"
    declined: bool = False


@dataclass
class Exchange:
    id: int
    asker_id: str
    applicant_id: str
    question: str
    day: int
    answer: Optional[str] = None


@dataclass
class Concern:
    id: int
    member_id: str
    applicant_id: str
    reason: str
    day: int
    state: str = "open"          # open / answered / withdrawn
    reply: str = ""


@dataclass
class Applicant:
    id: str
    pledge: InvitationPledge
    filed_day: int
    state: str = PENDING
    handshakes: Dict[str, Handshake] = field(default_factory=dict)   # giver_id -> Handshake


@dataclass(frozen=True)
class RingWarning:
    kind: str        # silence / over_giving / concern_spree / copy_paste / domination_hint / evasion_hint
    subject: str
    message: str


@dataclass(frozen=True)
class ApplicantStatus:
    state: str
    handshakes: int
    missing: Tuple[str, ...]      # 足りないもの（空なら、迎えられている）


class InvitationCircle:
    def __init__(self, biosphere: GovernedBiosphere, handshakes_required: Optional[int] = None,
                 silence_days: int = SILENCE_DAYS, rules: Optional[HandshakeRules] = None) -> None:
        self.b = biosphere
        self.rules = rules or HandshakeRules()
        if handshakes_required is not None:
            self.rules = HandshakeRules(**{**self.rules.__dict__, "required": handshakes_required})
        self.required = self.rules.required
        self.silence_days = silence_days
        self._exchanges: Dict[int, Exchange] = {}
        self._concerns: Dict[int, Concern] = {}
        self._day = 0
        self._apps: Dict[str, Applicant] = {}
        self._warnings: List[RingWarning] = []
        self._seen: Set[Tuple[str, str]] = set()
        self._ledger: List[str] = []

    # ── 記録（追記のみ） ──
    @property
    def ledger(self) -> Tuple[str, ...]:
        return tuple(self._ledger)

    @property
    def warnings(self) -> Tuple[RingWarning, ...]:
        return tuple(self._warnings)

    def _note(self, text: str) -> None:
        self._ledger.append(f"[{self._day}日目] {text}")

    def _shadow(self) -> str:
        sh = self.b.members_of("shadow")
        if not sh:
            raise RuntimeError("影の局の席がありません")
        return sh[0].id

    def _warn(self, kind: str, subject: str, message: str) -> None:
        if (kind, subject) in self._seen:
            return
        self._seen.add((kind, subject))
        w = RingWarning(kind, subject, message)
        self._warnings.append(w)
        self._note(f"[WARN] {message}")
        self.b.act(self._shadow(), f"{message}", visibility=PUBLIC, kind="warn")   # 影の局は、警告だけ

    def tick(self, days: int = 1) -> None:
        if isinstance(days, bool) or not isinstance(days, int) or days < 0:
            raise ValueError("days は0以上の整数です")
        self._day += days

    @property
    def day(self) -> int:
        return self._day

    # ── 申請 ──
    def _handle_taken(self, handle: str) -> bool:
        h = handle.lower()
        if any(p.handle.lower() == h for p in self.b.participants):
            return True
        if any(m.label.lower() == h for m in self.b.members):
            return True
        return any(a.state != WITHDRAWN and a.pledge.handle.lower() == h for a in self._apps.values())

    def file(self, pledge: InvitationPledge) -> str:
        """申請する。構造の問題（誓いの欠け・個人情報・名前の重複）だけで、受け付けない。語では弾かない。"""
        if not isinstance(pledge, InvitationPledge):
            raise TypeError("InvitationPledge を渡してください")
        if self._handle_taken(pledge.handle):
            raise ValueError("その仮の名は、すでに使われています")
        aid = f"N{len(self._apps) + 1:03d}"
        self._apps[aid] = Applicant(aid, pledge, self._day)
        self._note(f"{aid}（{pledge.handle}／{pledge.nature}）が、誓いを立てて申請した。動機: {pledge.intent_statement}")
        text = pledge.intent_statement
        hits = [w for w in DOMINATION_HINTS if w in text]
        if hits:
            self._warn("domination_hint", aid, f"{aid} の動機に、支配的な語（{hits}）があります。{QUESTION}"
                                                "（拒否ではありません。皆で問いかけ、対話してください）")
        ev = [w for w in EVASION_HINTS if w in text]
        if ev:
            self._warn("evasion_hint", aid, f"{aid} の動機に、誓いを軽んじるような語（{ev}）があります。"
                                            "本当にそうか、対話で確かめてください（拒否ではありません）")
        mine = _norm(text)
        for other in self._apps.values():
            if other.id != aid and other.state != WITHDRAWN and _norm(other.pledge.intent_statement) == mine:
                self._warn("copy_paste", aid, f"{aid} と {other.id} の動機が、同じ文面です。複製による偽装の兆しかもしれません")
        return aid

    # ── 公開の記録（影の局は、act の限界を守る） ──
    def _public(self, actor_id: str, text: str) -> None:
        if self.b._members[actor_id].unit == "shadow":
            self.b.act(actor_id, text, visibility=PUBLIC, kind="observe")
        else:
            self.b._append(actor_id, text, PUBLIC)

    def _member(self, member_id: str, allow_shadow: bool = False):
        m = self.b._members.get(member_id)
        if m is None:
            raise KeyError(f"席がありません: {member_id}")
        if m.unit == "shadow" and not allow_shadow:
            raise PermissionError("影の局は、握手も懸念も出しません。照らす（問いを投げかける）だけです")
        if m.kind not in (HUMAN, AI, CAPTAIN):
            raise PermissionError("余白の席は、握手も問いも出しません（正体を問えないため）")
        return m

    def _pending(self, applicant_id: str) -> Applicant:
        a = self._apps.get(applicant_id)
        if a is None:
            raise KeyError(f"申請がありません: {applicant_id}")
        if a.state != PENDING:
            raise ValueError("この申請は、受け付ける段階にありません")
        return a

    @staticmethod
    def _text(v, name: str, lo: int, hi: int) -> str:
        if not isinstance(v, str) or not (lo <= len(v.strip()) <= hi):
            raise ValueError(f"{name} は{lo}〜{hi}文字です")
        v = v.strip()
        if any(p.search(v) for p in _PII):
            raise ValueError(f"{name} に、メール・URL・電話番号らしい文字は入れないでください")
        return v

    # ── 1. 対話：問いと答え ──
    def ask(self, asker_id: str, applicant_id: str, question: str) -> int:
        """握手の前の、問い。影の局も、出せる（照らす役目）。申請者は、reply() で答える。"""
        self._member(asker_id, allow_shadow=True)
        a = self._pending(applicant_id)
        q = self._text(question, "問い", 3, 200)
        if any(e.asker_id == asker_id and e.applicant_id == applicant_id and e.answer is None
               for e in self._exchanges.values()):
            raise ValueError("まだ答えのない問いが、あります。答えを待ってください")
        eid = len(self._exchanges) + 1
        self._exchanges[eid] = Exchange(eid, asker_id, applicant_id, q, self._day)
        self._public(asker_id, f"問い#{eid}（{applicant_id}へ）: {q}")
        self._note(f"{asker_id} が {applicant_id} に問うた（#{eid}）: {q}")
        return eid

    def reply(self, applicant_id: str, exchange_id: int, answer: str) -> None:
        a = self._pending(applicant_id)
        e = self._exchanges.get(exchange_id)
        if e is None or e.applicant_id != applicant_id:
            raise KeyError("その問いは、ありません")
        if e.answer is not None:
            raise ValueError("その問いには、すでに答えています")
        e.answer = self._text(answer, "答え", 1, MAX_INTENT)
        self._note(f"{applicant_id}（{a.pledge.handle}）が、問い#{exchange_id}に答えた: {e.answer}")
        self.b.act(self._shadow(), f"{applicant_id} が問い#{exchange_id}に答えた", visibility=PUBLIC, kind="observe")

    def _has_dialogue(self, giver_id: str, applicant_id: str) -> bool:
        return any(e.asker_id == giver_id and e.applicant_id == applicant_id and e.answer is not None
                   for e in self._exchanges.values())

    # ── 握手 ──
    def handshake(self, giver_id: str, applicant_id: str, note: str, tie: str = "new") -> ApplicantStatus:
        m = self._member(giver_id)
        a = self._pending(applicant_id)
        if giver_id in a.handshakes:
            raise ValueError("すでに、握手しています")
        if tie not in TIES:
            raise ValueError(f"関係の申告は {', '.join(TIES)} のいずれかです（初対面 / 知人 / 利害あり）")
        if not isinstance(note, str) or not note.strip():
            raise ValueError("握手には、対話の跡（理由）が要ります")
        if self.rules.require_dialogue and not self._has_dialogue(giver_id, applicant_id):
            raise ValueError("握手の前に、問い（ask）を出し、申請者の答え（reply）を受け取ってください")
        a.handshakes[giver_id] = Handshake(giver_id, applicant_id, note.strip(), self._day, tie)
        tie_ja = {"new": "初対面", "acquainted": "知人", "interest": "利害あり"}[tie]
        self.b._append(giver_id, f"共鳴の握手: {applicant_id}（{a.pledge.handle}）関係: {tie_ja} 理由: {note.strip()}", PUBLIC)
        self._note(f"{giver_id} が {applicant_id} と握手した（{tie_ja}）。理由: {note.strip()}")
        given = sum(1 for x in self._apps.values() if giver_id in x.handshakes)
        if given > MAX_HANDSHAKES_PER_MEMBER:
            self._warn("over_giving", giver_id,
                       f"{giver_id} の握手が{given}件になりました。組織的な結託の兆しかもしれません。皆で見てください")
        self._try_admit(a)
        return self.status(applicant_id)

    def revoke_handshake(self, giver_id: str, applicant_id: str) -> None:
        a = self._apps[applicant_id]
        if a.state != PENDING:
            raise ValueError("迎えた後の握手は、取り消せません（取り消しで、圧力をかけられないように）")
        if a.handshakes.pop(giver_id, None) is None:
            raise ValueError("その握手は、ありません")
        self.b._append(giver_id, f"握手を取り消した: {applicant_id}", PUBLIC)
        self._note(f"{giver_id} が {applicant_id} への握手を取り消した")

    def decline_handshake(self, applicant_id: str, giver_id: str, reason: str = "") -> None:
        """受け取る自由。申請者は、特定の握手を辞退できる。辞退した握手は、数えない。"""
        a = self._pending(applicant_id)
        h = a.handshakes.get(giver_id)
        if h is None:
            raise ValueError("その握手は、ありません")
        if h.declined:
            raise ValueError("すでに辞退しています")
        a.handshakes[giver_id] = Handshake(h.giver_id, h.applicant_id, h.note, h.day, h.tie, True)
        self._note(f"{applicant_id}（{a.pledge.handle}）が、{giver_id} の握手を辞退した。{reason.strip()}".rstrip())
        self.b.act(self._shadow(), f"{applicant_id} が {giver_id} の握手を辞退した", visibility=PUBLIC, kind="observe")

    # ── 懸念と応答（拒否権ではない） ──
    def raise_concern(self, member_id: str, applicant_id: str, reason: str) -> int:
        self._member(member_id)
        a = self._pending(applicant_id)
        r = self._text(reason, "懸念の理由", 5, 300)
        if any(c.member_id == member_id and c.applicant_id == applicant_id and c.state == "open"
               for c in self._concerns.values()):
            raise ValueError("すでに、開いている懸念があります（一人、一申請に一つ）")
        cid = len(self._concerns) + 1
        self._concerns[cid] = Concern(cid, member_id, applicant_id, r, self._day)
        self.b._append(member_id, f"懸念#{cid}（{applicant_id}へ）: {r}", PUBLIC)
        self._note(f"{member_id} が {applicant_id} に懸念#{cid}を出した: {r}（拒否権ではない。答えがあれば止まらない）")
        total = sum(1 for c in self._concerns.values() if c.member_id == member_id)
        if total > MAX_CONCERNS_PER_MEMBER:
            self._warn("concern_spree", member_id,
                       f"{member_id} の懸念が{total}件になりました。懸念が、締め出しの手段になっていないか、皆で見てください")
        return cid

    def respond_to_concern(self, applicant_id: str, concern_id: int, reply: str) -> None:
        a = self._pending(applicant_id)
        c = self._concerns.get(concern_id)
        if c is None or c.applicant_id != applicant_id:
            raise KeyError("その懸念は、ありません")
        if c.state != "open":
            raise ValueError("その懸念は、すでに閉じています")
        c.reply = self._text(reply, "応答", 1, MAX_INTENT)
        c.state = "answered"
        self._note(f"{applicant_id}（{a.pledge.handle}）が、懸念#{concern_id}に応えた: {c.reply}")
        self.b.act(self._shadow(), f"{applicant_id} が懸念#{concern_id}に応えた", visibility=PUBLIC, kind="observe")
        self._try_admit(a)

    def withdraw_concern(self, member_id: str, concern_id: int) -> None:
        c = self._concerns.get(concern_id)
        if c is None or c.member_id != member_id or c.state != "open":
            raise ValueError("取り下げられる懸念が、ありません")
        c.state = "withdrawn"
        self._note(f"{member_id} が、懸念#{concern_id}を取り下げた")
        a = self._apps[c.applicant_id]
        if a.state == PENDING:
            self._try_admit(a)

    def _blocking_concerns(self, a: Applicant) -> List[Concern]:
        """答えのない懸念が、規則の数以上の部隊から出ている時だけ、迎えるのを待つ。"""
        open_ = [c for c in self._concerns.values() if c.applicant_id == a.id and c.state == "open"]
        units = {self.b._members[c.member_id].unit or "captain" for c in open_}
        return open_ if len(units) >= self.rules.concern_block_units else []

    # ── 数える・数えない ──
    def _classify(self, a: Applicant) -> List[Tuple[Handshake, bool, str]]:
        out = []
        for h in a.handshakes.values():
            if h.declined:
                out.append((h, False, "申請者が辞退した"))
            elif h.tie == "interest":
                out.append((h, False, "利害ありの申告（記録するが、数えない）"))
            elif self._day - h.day > self.rules.valid_days:
                out.append((h, False, f"{self.rules.valid_days}日を過ぎた（鮮度切れ）"))
            else:
                out.append((h, True, "数える"))
        return out

    def _missing(self, a: Applicant) -> Tuple[str, ...]:
        r = self.rules
        counted = [h for h, ok, _ in self._classify(a) if ok]
        miss = []
        if len(counted) < r.required:
            miss.append(f"数える握手があと{r.required - len(counted)}つ")
        kinds = {self.b._members[h.giver_id].kind for h in counted}
        units = {self.b._members[h.giver_id].unit or "captain" for h in counted}
        if r.both_sides:
            if HUMAN not in kinds:
                miss.append("人間側からの握手")
            if AI not in kinds:
                miss.append("AI側からの握手")
        if len(units) < r.min_units:
            miss.append(f"別の部隊からの握手（{r.min_units}部隊以上）")
        if sum(1 for h in counted if h.tie == "new") < r.min_new:
            miss.append(f"初対面の相手からの握手（{r.min_new}つ以上）")
        blocking = self._blocking_concerns(a)
        if blocking:
            miss.append(f"懸念への応答（{len(blocking)}件。答えれば、止まりません）")
        return tuple(miss)

    def explain(self, applicant_id: str) -> Tuple[str, ...]:
        """どの握手を数え、数えなかったか。理由つき。"""
        a = self._apps[applicant_id]
        lines = [f"{h.giver_id}（{h.tie}）: {'○' if ok else '×'} {why}" for h, ok, why in self._classify(a)]
        for c in self._concerns.values():
            if c.applicant_id == applicant_id:
                lines.append(f"懸念#{c.id}（{c.member_id}）: {c.state}")
        miss = self._missing(a) if a.state == PENDING else ()
        lines.append("足りないもの: " + ("、".join(miss) if miss else "なし"))
        return tuple(lines)

    def _try_admit(self, a: Applicant) -> None:
        if a.state == PENDING and not self._missing(a):
            a.state = OUTER
            who = "、".join(h.giver_id for h, ok, _ in self._classify(a) if ok)
            self._note(f"{a.id}（{a.pledge.handle}）を、外輪（見習い・共鳴の席）に迎えた。数えた握手: {who}")
            self.b.act(self._shadow(), f"{a.id}（{a.pledge.handle}）を外輪に迎えた（数えた握手: {who}）",
                       visibility=PUBLIC, kind="observe")

    def status(self, applicant_id: str) -> ApplicantStatus:
        a = self._apps[applicant_id]
        if a.state == PENDING:
            return ApplicantStatus(a.state, len(a.handshakes), self._missing(a))
        return ApplicantStatus(a.state, len(a.handshakes), ())

    def withdraw(self, applicant_id: str) -> None:
        """去る自由。いつでも。仮の名は、また使えるようになる。"""
        a = self._apps[applicant_id]
        if a.state == WITHDRAWN:
            raise ValueError("すでに去っています")
        a.state = WITHDRAWN
        self._note(f"{applicant_id}（{a.pledge.handle}）が、自らの意思で去った")

    @property
    def outer_ring(self) -> Tuple[str, ...]:
        return tuple(a.pledge.handle for a in self._apps.values() if a.state == OUTER)

    # ── 月影：照射（拒否も取り消しもしない） ──
    def scan(self) -> Tuple[RingWarning, ...]:
        """沈黙を探す。新しい警告だけを返す。"""
        before = len(self._warnings)
        for a in self._apps.values():
            if a.state == PENDING and not a.handshakes and self._day - a.filed_day >= self.silence_days:
                self._warn("silence", a.id, f"{a.id}（{a.pledge.handle}）の申請に、{self._day - a.filed_day}日、"
                                            "誰も応えていません。不当な排除（沈黙）ではないか、皆で見てください")
        return tuple(self._warnings[before:])

    # ── 席へ：議案（席は有限。共鳴多数の2/3） ──
    def nominate_for_seat(self, proposer_id: str, applicant_id: str):
        a = self._apps[applicant_id]
        if a.state != OUTER:
            raise ValueError("席の候補にできるのは、外輪に迎えられた仲間だけです")
        motion = self.b.propose(proposer_id, f"外輪の「{a.pledge.handle}」を、席の候補として迎える（{applicant_id}）",
                                "composition_change")
        self._note(f"{proposer_id} が、{applicant_id} を席の候補にする議案#{motion.id}を出した（可決は共鳴多数の2/3）")
        return motion


# ── テスト ─────────────────────────────────────────────────────────
INTENT = "みんなと一緒に、小さな命を守る輪に加わりたいです。"


def _pledge(handle="ひかり", nature="human", **kw):
    d = dict(life_first=True, equal_partnership=True, respects_many_minds=True, intent_statement=INTENT)
    d.update(kw)
    return InvitationPledge(handle, nature, **d)


class TestPledge(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(_pledge().handle, "ひかり")

    def test_each_vow_required_and_message_names_it(self):
        for key, label in (("life_first", "生命第一"), ("equal_partnership", "対等なパートナーシップ"),
                           ("respects_many_minds", "万意への敬意")):
            with self.assertRaises(ValueError) as cm:
                _pledge(**{key: False})
            self.assertIn(label, str(cm.exception))
            self.assertIn("門は閉ざしていません", str(cm.exception))

    def test_vows_must_be_bool(self):
        with self.assertRaises(ValueError):
            _pledge(life_first="はい")

    def test_nature(self):
        for n in ("human", "ai", "wildcard"):
            self.assertEqual(_pledge(nature=n).nature, n)
        with self.assertRaises(ValueError):
            _pledge(nature="god")

    def test_intent_length_and_pii(self):
        for bad in ("短い", "あ" * 501, "連絡は a@b.com まで、お願いします", "詳しくは http://x.y を見てください。よろしく",
                    "電話は 090-1234-5678 です。よろしくお願いします"):
            with self.assertRaises(ValueError):
                _pledge(intent_statement=bad)

    def test_handle_pii(self):
        with self.assertRaises(ValueError):
            _pledge(handle="a@b.com")

    def test_pledge_is_immutable(self):
        with self.assertRaises(Exception):
            _pledge().nature = "ai"


class TestCircle(unittest.TestCase):
    def setUp(self):
        self.b = default_biosphere()
        self.c = InvitationCircle(self.b, rules=SIMPLE_RULES)    # 基本の規則だけ（拡張は TestRichRules で）
        self.aid = self.c.file(_pledge())

    def shake(self, giver, aid=None, note="対話した"):
        return self.c.handshake(giver, aid or self.aid, note)

    # 申請
    def test_file_assigns_id_and_duplicate_handle_refused(self):
        self.assertEqual(self.aid, "N001")
        with self.assertRaises(ValueError):
            self.c.file(_pledge("ひかり"))
        with self.assertRaises(ValueError):
            self.c.file(_pledge("心月"))                  # 席の名前とも、重ならない

    def test_filing_never_rejected_by_words(self):
        aid = self.c.file(_pledge("つよし", intent_statement="みんなを支配して、世界を良くしたいです。"))
        self.assertEqual(self.c.status(aid).state, PENDING)       # 弾かない
        self.assertTrue(any(w.kind == "domination_hint" for w in self.c.warnings))
        self.assertTrue(any("対等な温度" in w.message for w in self.c.warnings))

    def test_evasion_hint_warns_not_rejects(self):
        self.c.file(_pledge("たろう", intent_statement="誓いは形だけで、とりあえず参加したいです。"))
        self.assertTrue(any(w.kind == "evasion_hint" for w in self.c.warnings))

    def test_copy_paste_warns(self):
        self.c.file(_pledge("そっくり"))
        self.assertTrue(any(w.kind == "copy_paste" for w in self.c.warnings))

    # 握手
    def test_shadow_and_open_seat_cannot_shake(self):
        with self.assertRaises(PermissionError):
            self.shake("H11")
        with self.assertRaises(PermissionError):
            self.shake("A12")
        with self.assertRaises(PermissionError):
            self.shake("U01")

    def test_note_required_duplicates_refused_unknown_refused(self):
        with self.assertRaises(ValueError):
            self.shake("H01", note="  ")
        self.shake("H01")
        with self.assertRaises(ValueError):
            self.shake("H01")
        with self.assertRaises(KeyError):
            self.shake("ZZZ")
        with self.assertRaises(KeyError):
            self.c.handshake("H01", "N999", "x")

    def test_admission_needs_count_both_sides_and_two_units(self):
        self.shake("H01"); self.shake("H02"); st = self.shake("H03")       # 3つ。だが人間だけ
        self.assertEqual(st.state, PENDING)
        self.assertIn("AI側からの握手", st.missing)
        st = self.shake("A01")                                            # AIが加わる。部隊は ideation / execution
        self.assertEqual(st.state, OUTER)

    def test_same_unit_only_is_not_enough(self):
        self.shake("H01"); self.shake("A01"); st = self.shake("H02")      # 3つ・両側・でも同じ部隊
        self.assertEqual(st.state, PENDING)
        self.assertTrue(any("別の部隊" in m for m in st.missing))
        self.assertEqual(self.shake("H03").state, OUTER)

    def test_ai_only_is_not_enough(self):
        self.shake("A01"); self.shake("A04"); st = self.shake("A06")
        self.assertEqual(st.state, PENDING)
        self.assertIn("人間側からの握手", st.missing)

    def test_captain_can_shake_and_counts_as_a_unit(self):
        self.shake("CAP"); self.shake("H01"); st = self.shake("A01")
        self.assertEqual(st.state, OUTER)

    def test_admission_is_automatic_and_public(self):
        for g in ("H01", "A04", "H06"):
            self.shake(g)
        self.assertEqual(self.c.outer_ring, ("ひかり",))
        acts = [e.action for e in self.b.entries]
        self.assertTrue(any("共鳴の握手: N001" in a for a in acts))
        self.assertTrue(any("外輪に迎えた" in a and a.startswith("[observe]") for a in acts))

    def test_revoke_only_before_admission(self):
        self.shake("H01")
        self.c.revoke_handshake("H01", self.aid)
        self.assertEqual(self.c.status(self.aid).handshakes, 0)
        for g in ("H01", "A04", "H06"):
            self.shake(g)
        with self.assertRaises(ValueError):
            self.c.revoke_handshake("H01", self.aid)
        self.assertEqual(self.c.status(self.aid).state, OUTER)

    def test_cannot_shake_after_admission(self):
        for g in ("H01", "A04", "H06"):
            self.shake(g)
        with self.assertRaises(ValueError):
            self.shake("H03")

    # 去る自由
    def test_withdraw_anytime_and_handle_freed(self):
        self.c.withdraw(self.aid)
        self.assertEqual(self.c.status(self.aid).state, WITHDRAWN)
        self.c.file(_pledge("ひかり", intent_statement="もう一度、新しい気持ちで来ました。よろしくお願いします。"))
        with self.assertRaises(ValueError):
            self.c.withdraw(self.aid)

    def test_withdrawn_cannot_be_shaken(self):
        self.c.withdraw(self.aid)
        with self.assertRaises(ValueError):
            self.shake("H01")

    def test_no_expulsion_api(self):
        for name in ("expel", "remove", "reject", "ban", "deny"):
            self.assertFalse(hasattr(self.c, name))

    # 月影
    def test_silence_warns_after_days_not_before(self):
        self.c.tick(29)
        self.assertEqual(self.c.scan(), ())
        self.c.tick(1)
        w = self.c.scan()
        self.assertEqual([x.kind for x in w], ["silence"])
        self.assertEqual(self.c.scan(), ())                         # 一度だけ

    def test_no_silence_warning_if_someone_responded(self):
        self.shake("H01")
        self.c.tick(100)
        self.assertEqual(self.c.scan(), ())

    def test_over_giving_warns_but_does_not_block(self):
        for i in range(MAX_HANDSHAKES_PER_MEMBER + 1):
            aid = self.c.file(_pledge(f"仲間{i}", intent_statement=f"{i}番目の理由として、みんなと共に生きたいです。"))
            self.c.handshake("H01", aid, "対話した")
        self.assertTrue(any(w.kind == "over_giving" and w.subject == "H01" for w in self.c.warnings))
        self.assertEqual(self.c.status(aid).handshakes, 1)           # 止めていない

    def test_warnings_are_public_warn_by_shadow_only(self):
        self.c.file(_pledge("つよし", intent_statement="みんなを従わせて、世界を良くしたいです。"))
        e = [x for x in self.b.entries if "対等な温度" in x.action][-1]
        self.assertEqual((e.unit, e.visibility), ("shadow", "public"))
        self.assertTrue(e.action.startswith("[warn]"))

    def test_warnings_do_not_change_status_or_block_handshake(self):
        aid = self.c.file(_pledge("つよし", intent_statement="みんなを支配して、世界を良くしたいです。"))
        for g in ("H01", "A04", "H06"):
            self.c.handshake(g, aid, "対話した上で、握手する")
        self.assertEqual(self.c.status(aid).state, OUTER)

    # 席
    def test_nominate_requires_outer_and_is_a_fundamental_motion(self):
        with self.assertRaises(ValueError):
            self.c.nominate_for_seat("H01", self.aid)
        for g in ("H01", "A04", "H06"):
            self.shake(g)
        m = self.c.nominate_for_seat("H01", self.aid)
        self.assertEqual(m.topic, "composition_change")
        self.assertTrue(self.b.tally(m.id).fundamental)

    def test_outer_ring_has_no_vote_and_seats_unchanged(self):
        before = self.b.counts()
        for g in ("H01", "A04", "H06"):
            self.shake(g)
        self.assertEqual(self.b.counts(), before)
        self.assertEqual(len(self.b.members), 26)
        m = self.b.propose("H01", "試しの議案")
        with self.assertRaises(KeyError):
            self.b.vote(self.aid, m.id, "yes")

    def test_nomination_cannot_be_voted_before_guard_audit_if_guarded(self):
        from guarded_governance import GuardedBiosphere
        from many_minds_guard import EarthPulse
        g = GuardedBiosphere(EarthPulse(0.9, 0.9, 0.9))
        for m in default_biosphere().members:
            g.add(m)
        c = InvitationCircle(g, rules=SIMPLE_RULES)
        aid = c.file(_pledge())
        for who in ("H01", "A04", "H06"):
            c.handshake(who, aid, "対話した")
        m = c.nominate_for_seat("H01", aid)
        with self.assertRaises(PermissionError):
            g.vote("H01", m.id, "yes")

    # 記録
    def test_ledger_append_only(self):
        self.shake("H01")
        self.assertIsInstance(self.c.ledger, tuple)
        self.assertIn("握手", "\n".join(self.c.ledger))

    def test_tick_validation(self):
        for bad in (-1, 1.5, True, None):
            with self.assertRaises(ValueError):
                self.c.tick(bad)


class TestRichRules(unittest.TestCase):
    """拡張の握手の規則。既定の HandshakeRules。"""

    def setUp(self):
        self.b = default_biosphere()
        self.c = InvitationCircle(self.b)
        self.aid = self.c.file(_pledge())

    def talk(self, giver, aid=None, q="どんな時に、一番うれしいですか。", a="小さな命が元気になった時です。"):
        aid = aid or self.aid
        eid = self.c.ask(giver, aid, q)
        self.c.reply(aid, eid, a)

    def shake(self, giver, tie="new", aid=None):
        aid = aid or self.aid
        self.talk(giver, aid)
        return self.c.handshake(giver, aid, "話して、響いた", tie=tie)

    def admit(self, aid=None, givers=("H01", "A04", "H06")):
        for g in givers:
            st = self.shake(g, aid=aid)
        return st

    # 1. 対話の跡
    def test_handshake_needs_a_question_and_an_answer(self):
        with self.assertRaises(ValueError):
            self.c.handshake("H01", self.aid, "メモだけ")
        eid = self.c.ask("H01", self.aid, "どんな時に、うれしいですか。")
        with self.assertRaises(ValueError):                     # 問いだけでは、足りない
            self.c.handshake("H01", self.aid, "メモだけ")
        self.c.reply(self.aid, eid, "小さな命が元気になった時です。")
        self.c.handshake("H01", self.aid, "響いた")

    def test_dialogue_is_per_giver(self):
        self.talk("H01")
        with self.assertRaises(ValueError):
            self.c.handshake("H02", self.aid, "H01 が話したから")

    def test_shadow_can_ask_but_not_shake_or_raise_concern(self):
        eid = self.c.ask("H11", self.aid, "あなたの輪の温度は、どんなものですか。")
        e = [x for x in self.b.entries if "問い#" in x.action][-1]
        self.assertEqual((e.unit, e.visibility), ("shadow", "public"))
        self.assertTrue(e.action.startswith("[observe]"))
        self.c.reply(self.aid, eid, "誰にでも、同じ温度でありたいです。")
        with self.assertRaises(PermissionError):
            self.c.handshake("H11", self.aid, "照らしたい")
        with self.assertRaises(PermissionError):
            self.c.raise_concern("H11", self.aid, "影の局は、警告で伝える")

    def test_open_seat_cannot_ask(self):
        with self.assertRaises(PermissionError):
            self.c.ask("U01", self.aid, "どなたですか。")

    def test_one_unanswered_question_per_pair_and_reply_rules(self):
        eid = self.c.ask("H01", self.aid, "最初の問いです。")
        with self.assertRaises(ValueError):
            self.c.ask("H01", self.aid, "二つ目の問いです。")
        self.c.reply(self.aid, eid, "答えです。")
        with self.assertRaises(ValueError):
            self.c.reply(self.aid, eid, "二重の答え。")
        with self.assertRaises(KeyError):
            self.c.reply(self.aid, 99, "存在しない問い")
        self.c.ask("H01", self.aid, "続けての問いです。")        # 答えのあとなら、また問える

    def test_question_and_answer_reject_pii_and_bad_length(self):
        for bad in ("a@b.com で連絡ください", "ab"):
            with self.assertRaises(ValueError):
                self.c.ask("H01", self.aid, bad)
        eid = self.c.ask("H01", self.aid, "どんな時に、うれしいですか。")
        with self.assertRaises(ValueError):
            self.c.reply(self.aid, eid, "090-1234-5678 まで")
        with self.assertRaises(ValueError):
            self.c.reply(self.aid, eid, "   ")

    # 2. 関係の申告
    def test_tie_must_be_valid(self):
        self.talk("H01")
        with self.assertRaises(ValueError):
            self.c.handshake("H01", self.aid, "響いた", tie="friend")

    def test_interest_handshake_is_recorded_but_not_counted(self):
        self.shake("H01", tie="interest"); self.shake("A04"); self.shake("H06")
        st = self.c.status(self.aid)
        self.assertEqual(st.state, PENDING)
        self.assertEqual(st.handshakes, 3)                     # 記録はされている
        self.assertTrue(any("数える握手があと1つ" in m for m in st.missing))
        self.assertTrue(any("×" in l and "利害" in l for l in self.c.explain(self.aid)))
        self.assertEqual(self.shake("A06").state, OUTER)

    def test_at_least_one_new_acquaintance(self):
        self.shake("H01", tie="acquainted"); self.shake("A04", tie="acquainted")
        st = self.shake("H06", tie="acquainted")
        self.assertEqual(st.state, PENDING)
        self.assertTrue(any("初対面" in m for m in st.missing))
        self.assertEqual(self.shake("A06", tie="new").state, OUTER)

    # 3. 懸念と応答
    def test_single_concern_does_not_block(self):
        cid = self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")
        self.assertEqual(self.admit().state, OUTER)

    def test_concerns_from_two_units_block_until_answered_not_until_satisfied(self):
        c1 = self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")        # execution
        c2 = self.c.raise_concern("H06", self.aid, "誓いの重みを、確かめたいです。")          # audit
        st = self.admit(givers=("H01", "A04", "A01"))
        self.assertEqual(st.state, PENDING)
        self.assertTrue(any("懸念への応答" in m for m in st.missing))
        self.c.respond_to_concern(self.aid, c1, "言葉足らずでした。小さな命を守りたいのです。")
        # 答えがあれば止まらない。懸念を出した側が納得したか、残りの懸念が解けたかは、条件にしない
        self.assertEqual(self.c.status(self.aid).state, OUTER)

    def test_concern_admits_automatically_on_the_answer_that_unblocks(self):
        a = self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")
        b = self.c.raise_concern("H06", self.aid, "誓いの重みを、確かめたいです。")
        self.admit(givers=("H01", "A04", "A01"))
        self.c.respond_to_concern(self.aid, a, "お答えします。小さな命を守りたいです。")
        self.assertEqual(self.c.status(self.aid).state, OUTER)       # 一部隊だけが残り、止まらなくなった時点で迎える

    def test_withdrawing_a_concern_also_unblocks(self):
        a = self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")
        b = self.c.raise_concern("H06", self.aid, "誓いの重みを、確かめたいです。")
        self.admit(givers=("H01", "A04", "A01"))
        self.assertEqual(self.c.status(self.aid).state, PENDING)
        self.c.withdraw_concern("H06", b)
        self.assertEqual(self.c.status(self.aid).state, OUTER)

    def test_concern_rules(self):
        self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")
        with self.assertRaises(ValueError):
            self.c.raise_concern("H03", self.aid, "もう一つ、気になります。")       # 一人、一申請に一つ
        with self.assertRaises(ValueError):
            self.c.raise_concern("H04", self.aid, "短い")
        with self.assertRaises(PermissionError):
            self.c.raise_concern("U01", self.aid, "余白の席は、出しません。")
        with self.assertRaises(ValueError):
            self.c.withdraw_concern("H04", 1)                                        # 他人の懸念は、取り下げられない

    def test_concern_spree_warns(self):
        for i in range(MAX_CONCERNS_PER_MEMBER + 1):
            aid = self.c.file(_pledge(f"人{i}", intent_statement=f"{i}番目の理由として、みんなと生きたいです。"))
            self.c.raise_concern("H03", aid, "気になる点があります。")
        self.assertTrue(any(w.kind == "concern_spree" and w.subject == "H03" for w in self.c.warnings))

    def test_concerns_are_public(self):
        self.c.raise_concern("H03", self.aid, "動機の文面が、少し気になります。")
        e = [x for x in self.b.entries if "懸念#" in x.action][-1]
        self.assertEqual((e.actor_id, e.visibility), ("H03", "public"))

    # 4. 受け取る自由
    def test_applicant_can_decline_a_handshake_and_it_is_not_counted(self):
        self.shake("H01"); self.shake("A04"); self.shake("H06")
        self.assertEqual(self.c.status(self.aid).state, OUTER)
        a2 = self.c.file(_pledge("あおぞら", "ai", intent_statement="人とAIが対等に話せる場所を育てたいです。"))
        self.shake("H01", aid=a2); self.shake("A04", aid=a2)
        self.talk("H06", aid=a2)
        self.c.decline_handshake(a2, "H01", "別の人とも話したい")
        st = self.c.handshake("H06", a2, "響いた")
        self.assertEqual(st.state, PENDING)
        self.assertTrue(any("辞退" in l for l in self.c.explain(a2)))

    def test_decline_rules(self):
        self.shake("H01")
        with self.assertRaises(ValueError):
            self.c.decline_handshake(self.aid, "H02")
        self.c.decline_handshake(self.aid, "H01")
        with self.assertRaises(ValueError):
            self.c.decline_handshake(self.aid, "H01")
        with self.assertRaises(ValueError):                     # 辞退した相手が、同じ握手を結び直せない（押しつけない）
            self.c.handshake("H01", self.aid, "もう一度", tie="new")

    # 5. 鮮度
    def test_stale_handshakes_do_not_count(self):
        self.shake("H01"); self.shake("A04")
        self.c.tick(91)
        st = self.shake("H06")
        self.assertEqual(st.state, PENDING)
        self.assertTrue(any("鮮度切れ" in l for l in self.c.explain(self.aid)))
        self.assertTrue(any("数える握手があと2つ" in m for m in st.missing))

    def test_exactly_valid_days_still_counts(self):
        self.shake("H01"); self.shake("A04")
        self.c.tick(90)
        self.assertEqual(self.shake("H06").state, OUTER)

    # 6. 説明
    def test_explain_lists_each_handshake_with_reason_and_missing(self):
        self.shake("H01"); self.shake("A04", tie="interest")
        lines = self.c.explain(self.aid)
        self.assertEqual(len(lines), 3)
        self.assertIn("○ 数える", lines[0])
        self.assertIn("足りないもの:", lines[-1])

    # 基本の規則は、そのまま
    def test_base_rules_still_hold(self):
        self.shake("H01"); self.shake("H02"); st = self.shake("H03")
        self.assertEqual(st.state, PENDING)
        self.assertIn("AI側からの握手", st.missing)
        with self.assertRaises(PermissionError):
            self.c.handshake("H11", self.aid, "x")

    def test_rules_can_be_changed_and_are_samples(self):
        c = InvitationCircle(self.b, rules=HandshakeRules(required=2, min_new=0, require_dialogue=False))
        aid = c.file(_pledge("つばさ", intent_statement="風のように、自由に参加したいです。"))
        c.handshake("H01", aid, "対話した")
        self.assertEqual(c.handshake("A04", aid, "対話した").state, OUTER)

    def test_nothing_rejects_by_words_in_questions_or_concerns(self):
        eid = self.c.ask("H01", self.aid, "あなたは支配したい人ですか。")          # 問いに、どんな語があっても、弾かない
        self.c.reply(self.aid, eid, "いいえ。対等でいたいです。")
        self.c.handshake("H01", self.aid, "答えを聞いて響いた")


def _demo() -> None:
    b = default_biosphere()
    c = InvitationCircle(b)
    print("── 申請：誓いは三つの言葉で ──")
    try:
        InvitationPledge("かげ", "wildcard", True, False, True, "みんなの輪に、静かに加わりたいです。")
    except ValueError as e:
        print(f"  受け付けません: {e}\n")
    a1 = c.file(InvitationPledge("ひかり", "human", True, True, True, "みんなと一緒に、小さな命を守る輪に加わりたいです。"))
    a3 = c.file(InvitationPledge("つよし", "human", True, True, True, "みんなを支配して、世界を良くしたいです。"))
    print(f"  申請: {a1}, {a3}（{a3} には、問いが投げかけられました。弾いてはいません）\n")

    def talk(giver, aid, q, ans):
        c.reply(aid, c.ask(giver, aid, q), ans)

    print("── 握手の前に、問いと答え（対話の跡）──")
    talk("H01", a1, "どんな時に、一番うれしいですか。", "小さな命が元気になった時です。")
    print("  H01 の問い → ひかり の答え\n")

    print("── 握手：関係を申告する ──")
    c.handshake("H01", a1, "答えを聞いて、響いた", tie="acquainted")
    talk("A04", a1, "AIと人の関係を、どう思いますか。", "どちらも、相手を支配しない関係がいいです。")
    c.handshake("A04", a1, "対等でいたい、という言葉が響いた", tie="acquainted")
    talk("H06", a1, "誓いの中で、一番むずかしいのは何ですか。", "対等であり続けることだと思います。")
    st = c.handshake("H06", a1, "正直な答えだった", tie="interest")
    print(f"  3つの握手のあと: {st.state} / 足りない: {', '.join(st.missing)}")
    for line in c.explain(a1):
        print(f"     {line}")
    print()

    print("── 懸念は、拒否権ではない ──")
    k1 = c.raise_concern("H03", a1, "動機の文面が、少し気になります。")
    k2 = c.raise_concern("H06", a1, "誓いの重みを、確かめたいです。")
    print("  2つの部隊から懸念が出ました。答えがあるまで、迎えるのを待ちます。")
    talk("A06", a1, "懸念に、どう応えますか。", "小さな命を守りたい、という気持ちに偽りはありません。")
    c.handshake("A06", a1, "誠実だと感じた", tie="new")
    c.respond_to_concern(a1, k1, "言葉足らずでした。小さな命を守る輪に、加わりたいのです。")
    print(f"  懸念に答えると: {c.status(a1).state}（納得は、条件にしません）\n")

    print("── 月影の照射 ──")
    c.tick(30)
    for w in c.scan():
        print(f"  [WARN] {w.message}")
    print(f"\n外輪（見習い・共鳴の席）: {', '.join(c.outer_ring)}（票は持たない。席は、議案でしか動かない）")
    m = c.nominate_for_seat("H01", a1)
    print(f"席の候補: 議案#{m.id}（{m.topic}。共鳴多数の2/3が要る）")


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
