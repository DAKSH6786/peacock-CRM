"""Prompt Universe Intelligence orchestration service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.prompt_universe import (
    FUNNEL_STAGES,
    PROMPT_SOURCE_KINDS,
    PROMPT_TYPES,
    PromptFamily,
    PromptGenerationRun,
    PromptSourceSignal,
    PromptUniverse,
    SyntheticPersona,
    UniversePrompt,
)
from prompt_universe.generator import (
    default_personas_for_codes,
    expand_signal,
    prompt_hash,
    slugify,
)
from prompt_universe.models import GenerateUniverseSpec, SourceSignalSpec, UniverseSummary
from prompt_universe.personas import SYNTHETIC_PERSONA_CATALOG


class PromptUniverseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_and_generate(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: GenerateUniverseSpec,
        created_by: str | None = None,
    ) -> UniverseSummary:
        if not spec.signals:
            raise ValueError("At least one source signal is required to grow a Prompt Universe")
        if spec.max_prompts < 1:
            raise ValueError("max_prompts must be >= 1")

        for signal in spec.signals:
            if signal.source_kind not in PROMPT_SOURCE_KINDS:
                raise ValueError(f"Unknown source_kind: {signal.source_kind}")

        universe = PromptUniverse(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            brand_name=spec.brand_name,
            industry=spec.industry,
            primary_location=spec.primary_location,
            description=spec.description,
            notes=spec.notes,
            generation_status="generating",
        )
        self.db.add(universe)
        self.db.flush()

        run = PromptGenerationRun(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            universe_id=universe.id,
            started_at=datetime.now(UTC),
            run_status="running",
        )
        self.db.add(run)
        self.db.flush()

        try:
            personas = self._materialise_personas(
                universe=universe,
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                codes=spec.persona_codes,
            )
            persona_by_code = {p.code: p for p in personas}

            signal_rows: list[PromptSourceSignal] = []
            for signal in spec.signals:
                row = PromptSourceSignal(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    universe_id=universe.id,
                    source_kind=signal.source_kind,
                    signal_text=signal.signal_text.strip(),
                    signal_key=slugify(f"{signal.source_kind}-{signal.signal_text}")[:240],
                    weight=signal.weight,
                    location_code=signal.location_code or spec.primary_location,
                    product_name=signal.product_name,
                    topic_hint=signal.topic_hint,
                    external_ref=signal.external_ref,
                )
                self.db.add(row)
                signal_rows.append(row)
            self.db.flush()

            catalog_personas = default_personas_for_codes(spec.persona_codes)
            families: dict[str, PromptFamily] = {}
            seen: set[tuple[str, str]] = set()
            created_prompts = 0
            created_families = 0

            for signal_row, signal_spec in zip(signal_rows, spec.signals, strict=True):
                expansion = expand_signal(
                    signal_text=signal_spec.signal_text,
                    source_kind=signal_spec.source_kind,
                    brand_name=spec.brand_name,
                    industry=spec.industry,
                    location=signal_spec.location_code or spec.primary_location,
                    product_name=signal_spec.product_name,
                    topic_hint=signal_spec.topic_hint,
                    weight=signal_spec.weight,
                    personas=catalog_personas,
                    include_persona_variants=spec.include_persona_variants,
                )
                for generated in expansion.prompts:
                    if created_prompts >= spec.max_prompts:
                        break
                    ph = prompt_hash(generated.prompt_text)
                    key = (ph, generated.persona_code)
                    if key in seen:
                        continue
                    seen.add(key)

                    family = families.get(generated.family_slug)
                    if family is None:
                        family = PromptFamily(
                            id=new_uuid(),
                            organisation_id=organisation_id,
                            workspace_id=workspace_id,
                            created_by=created_by,
                            universe_id=universe.id,
                            seed_signal_id=signal_row.id,
                            name=generated.family_name,
                            slug=generated.family_slug,
                            topic=generated.family_topic,
                            summary=f"Intent family expanded from {signal_spec.source_kind}",
                            member_count=0,
                        )
                        self.db.add(family)
                        self.db.flush()
                        families[generated.family_slug] = family
                        created_families += 1

                    persona_row = persona_by_code.get(generated.persona_code)
                    prompt = UniversePrompt(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        universe_id=universe.id,
                        family_id=family.id,
                        persona_id=persona_row.id if persona_row else None,
                        prompt_text=generated.prompt_text,
                        prompt_hash=ph,
                        topic=generated.topic,
                        subtopic=generated.subtopic,
                        intent=generated.intent,
                        persona_code=generated.persona_code,
                        funnel_stage=generated.funnel_stage,
                        location=generated.location,
                        product=generated.product,
                        problem=generated.problem,
                        commercial_value=generated.commercial_value,
                        brand_relevance=generated.brand_relevance,
                        prompt_type=generated.prompt_type,
                        source_kind=generated.source_kind,
                        complexity=generated.complexity,
                        is_tracked=generated.complexity == "simple"
                        and generated.prompt_type in {"recommendation", "comparison", "pricing"},
                        priority=generated.priority,
                    )
                    self.db.add(prompt)
                    family.member_count += 1
                    created_prompts += 1

                if created_prompts >= spec.max_prompts:
                    break

            universe.prompt_count = created_prompts
            universe.family_count = created_families
            universe.signal_count = len(signal_rows)
            universe.generation_status = "ready"

            run.signals_consumed = len(signal_rows)
            run.prompts_created = created_prompts
            run.families_created = created_families
            run.personas_materialised = len(personas)
            run.run_status = "completed"
            run.completed_at = datetime.now(UTC)

            self.db.commit()
            return self.summarise(universe.id, organisation_id)
        except Exception as exc:  # noqa: BLE001
            run.run_status = "failed"
            run.error_summary = str(exc)[:2000]
            run.completed_at = datetime.now(UTC)
            universe.generation_status = "failed"
            self.db.commit()
            raise

    def _materialise_personas(
        self,
        *,
        universe: PromptUniverse,
        organisation_id: str,
        workspace_id: str,
        created_by: str | None,
        codes: list[str] | None,
    ) -> list[SyntheticPersona]:
        selected = default_personas_for_codes(codes)
        rows: list[SyntheticPersona] = []
        for entry in selected:
            row = SyntheticPersona(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                universe_id=universe.id,
                code=entry.code,
                name=entry.name,
                description=entry.description,
                query_style=entry.query_style,
                is_system_seed=True,
                context_template=entry.context_template,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def summarise(self, universe_id: str, organisation_id: str) -> UniverseSummary:
        universe = self.db.scalar(
            select(PromptUniverse).where(
                PromptUniverse.id == universe_id,
                PromptUniverse.organisation_id == organisation_id,
            )
        )
        if universe is None:
            raise LookupError("Prompt universe not found")

        type_rows = self.db.execute(
            select(UniversePrompt.prompt_type, func.count())
            .where(UniversePrompt.universe_id == universe_id)
            .group_by(UniversePrompt.prompt_type)
        ).all()
        type_counts = {str(k): int(v) for k, v in type_rows}

        simple_count = self.db.scalar(
            select(func.count())
            .select_from(UniversePrompt)
            .where(
                UniversePrompt.universe_id == universe_id,
                UniversePrompt.complexity == "simple",
            )
        ) or 0
        contextual_count = self.db.scalar(
            select(func.count())
            .select_from(UniversePrompt)
            .where(
                UniversePrompt.universe_id == universe_id,
                UniversePrompt.complexity == "contextual",
            )
        ) or 0
        persona_count = self.db.scalar(
            select(func.count())
            .select_from(SyntheticPersona)
            .where(SyntheticPersona.universe_id == universe_id)
        ) or 0

        return UniverseSummary(
            universe_id=universe.id,
            name=universe.name,
            brand_name=universe.brand_name,
            generation_status=universe.generation_status,
            prompt_count=universe.prompt_count,
            family_count=universe.family_count,
            signal_count=universe.signal_count,
            persona_count=int(persona_count),
            prompt_type_counts=type_counts,
            simple_count=int(simple_count),
            contextual_count=int(contextual_count),
        )

    def list_prompts(
        self,
        *,
        universe_id: str,
        organisation_id: str,
        prompt_type: str | None = None,
        persona_code: str | None = None,
        complexity: str | None = None,
        tracked_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UniversePrompt]:
        universe = self.db.scalar(
            select(PromptUniverse).where(
                PromptUniverse.id == universe_id,
                PromptUniverse.organisation_id == organisation_id,
            )
        )
        if universe is None:
            raise LookupError("Prompt universe not found")

        stmt = select(UniversePrompt).where(UniversePrompt.universe_id == universe_id)
        if prompt_type:
            stmt = stmt.where(UniversePrompt.prompt_type == prompt_type)
        if persona_code:
            stmt = stmt.where(UniversePrompt.persona_code == persona_code)
        if complexity:
            stmt = stmt.where(UniversePrompt.complexity == complexity)
        if tracked_only:
            stmt = stmt.where(UniversePrompt.is_tracked.is_(True))
        stmt = stmt.order_by(UniversePrompt.commercial_value.desc()).offset(offset).limit(min(limit, 500))
        return list(self.db.scalars(stmt).all())

    def list_personas(self, *, universe_id: str, organisation_id: str) -> list[SyntheticPersona]:
        universe = self.db.scalar(
            select(PromptUniverse).where(
                PromptUniverse.id == universe_id,
                PromptUniverse.organisation_id == organisation_id,
            )
        )
        if universe is None:
            raise LookupError("Prompt universe not found")
        return list(
            self.db.scalars(
                select(SyntheticPersona)
                .where(SyntheticPersona.universe_id == universe_id)
                .order_by(SyntheticPersona.code)
            ).all()
        )

    def catalog(self) -> dict:
        return {
            "prompt_types": list(PROMPT_TYPES),
            "source_kinds": list(PROMPT_SOURCE_KINDS),
            "funnel_stages": list(FUNNEL_STAGES),
            "synthetic_personas": [
                {
                    "code": e.code,
                    "name": e.name,
                    "description": e.description,
                    "query_style": e.query_style,
                }
                for e in SYNTHETIC_PERSONA_CATALOG.values()
            ],
        }

    def add_signals_and_expand(
        self,
        *,
        universe_id: str,
        organisation_id: str,
        signals: list[SourceSignalSpec],
        include_persona_variants: bool = True,
        max_new_prompts: int = 200,
        created_by: str | None = None,
    ) -> UniverseSummary:
        universe = self.db.scalar(
            select(PromptUniverse).where(
                PromptUniverse.id == universe_id,
                PromptUniverse.organisation_id == organisation_id,
            )
        )
        if universe is None:
            raise LookupError("Prompt universe not found")
        if not signals:
            raise ValueError("signals required")

        personas = list(
            self.db.scalars(
                select(SyntheticPersona).where(SyntheticPersona.universe_id == universe_id)
            ).all()
        )
        catalog = default_personas_for_codes([p.code for p in personas] or None)
        persona_by_code = {p.code: p for p in personas}

        run = PromptGenerationRun(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=universe.workspace_id,
            created_by=created_by,
            universe_id=universe.id,
            started_at=datetime.now(UTC),
            run_status="running",
        )
        self.db.add(run)
        self.db.flush()

        existing_hashes = {
            (h, c)
            for h, c in self.db.execute(
                select(UniversePrompt.prompt_hash, UniversePrompt.persona_code).where(
                    UniversePrompt.universe_id == universe_id
                )
            ).all()
        }
        families = {
            f.slug: f
            for f in self.db.scalars(
                select(PromptFamily).where(PromptFamily.universe_id == universe_id)
            ).all()
        }

        created_prompts = 0
        created_families = 0
        for signal in signals:
            if signal.source_kind not in PROMPT_SOURCE_KINDS:
                raise ValueError(f"Unknown source_kind: {signal.source_kind}")
            row = PromptSourceSignal(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=universe.workspace_id,
                created_by=created_by,
                universe_id=universe.id,
                source_kind=signal.source_kind,
                signal_text=signal.signal_text.strip(),
                signal_key=slugify(f"{signal.source_kind}-{signal.signal_text}")[:240],
                weight=signal.weight,
                location_code=signal.location_code or universe.primary_location,
                product_name=signal.product_name,
                topic_hint=signal.topic_hint,
                external_ref=signal.external_ref,
            )
            self.db.add(row)
            self.db.flush()
            universe.signal_count += 1

            expansion = expand_signal(
                signal_text=signal.signal_text,
                source_kind=signal.source_kind,
                brand_name=universe.brand_name,
                industry=universe.industry,
                location=signal.location_code or universe.primary_location,
                product_name=signal.product_name,
                topic_hint=signal.topic_hint,
                weight=signal.weight,
                personas=catalog,
                include_persona_variants=include_persona_variants,
            )
            for generated in expansion.prompts:
                if created_prompts >= max_new_prompts:
                    break
                ph = prompt_hash(generated.prompt_text)
                key = (ph, generated.persona_code)
                if key in existing_hashes:
                    continue
                existing_hashes.add(key)

                family = families.get(generated.family_slug)
                if family is None:
                    family = PromptFamily(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=universe.workspace_id,
                        created_by=created_by,
                        universe_id=universe.id,
                        seed_signal_id=row.id,
                        name=generated.family_name,
                        slug=generated.family_slug,
                        topic=generated.family_topic,
                        summary=f"Intent family expanded from {signal.source_kind}",
                        member_count=0,
                    )
                    self.db.add(family)
                    self.db.flush()
                    families[generated.family_slug] = family
                    created_families += 1
                    universe.family_count += 1

                persona_row = persona_by_code.get(generated.persona_code)
                self.db.add(
                    UniversePrompt(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=universe.workspace_id,
                        created_by=created_by,
                        universe_id=universe.id,
                        family_id=family.id,
                        persona_id=persona_row.id if persona_row else None,
                        prompt_text=generated.prompt_text,
                        prompt_hash=ph,
                        topic=generated.topic,
                        subtopic=generated.subtopic,
                        intent=generated.intent,
                        persona_code=generated.persona_code,
                        funnel_stage=generated.funnel_stage,
                        location=generated.location,
                        product=generated.product,
                        problem=generated.problem,
                        commercial_value=generated.commercial_value,
                        brand_relevance=generated.brand_relevance,
                        prompt_type=generated.prompt_type,
                        source_kind=generated.source_kind,
                        complexity=generated.complexity,
                        is_tracked=False,
                        priority=generated.priority,
                    )
                )
                family.member_count += 1
                created_prompts += 1
                universe.prompt_count += 1

        run.signals_consumed = len(signals)
        run.prompts_created = created_prompts
        run.families_created = created_families
        run.personas_materialised = 0
        run.run_status = "completed"
        run.completed_at = datetime.now(UTC)
        self.db.commit()
        return self.summarise(universe_id, organisation_id)
