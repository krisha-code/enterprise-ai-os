class EvidenceSufficiencyService:
    """
    Evaluates whether retrieved and reranked evidence
    is strong enough to continue to answer generation.
    """

    @staticmethod
    def is_sufficient(
        best_score: float | None,
        average_top_3: float | None,
        count_ge_2: int,
        dominant_section_count: int,
    ) -> bool:
        """
        Apply the evidence sufficiency rules.

        Parameters
        ----------
        best_score:
            Highest reranker score among retrieved results.

        average_top_3:
            Average reranker score of the top 3 results.

        count_ge_2:
            Number of retrieved results whose reranker
            score is at least 2.0.

        dominant_section_count:
            Number of top results belonging to the most
            common section.
        """

        # No meaningful score means we do not have
        # sufficient evidence.
        if best_score is None:
            return False

        if average_top_3 is None:
            return False

        # --------------------------------------------------
        # Rule 1
        #
        # Multiple reasonably strong results combined
        # with a strong average top-3 score.
        # --------------------------------------------------

        if (
            count_ge_2 >= 2
            and average_top_3 >= 3.0
        ):
            return True

        # --------------------------------------------------
        # Rule 2
        #
        # One very strong result plus at least one
        # reasonably relevant result.
        # --------------------------------------------------

        if (
            best_score >= 8.0
            and count_ge_2 >= 1
        ):
            return True

        # --------------------------------------------------
        # Rule 3
        #
        # Several results concentrated in the same section
        # can indicate coherent evidence.
        #
        # We also require the best score to be positive
        # enough to avoid accepting arbitrary section
        # concentration.
        # --------------------------------------------------

        if (
            dominant_section_count >= 4
            and best_score >= 1.0
        ):
            return True

        return False

    @staticmethod
    def evaluate(reranked_results) -> bool:
        """
        Evaluate the evidence directly from reranked results.

        Parameters
        ----------
        reranked_results:
            A list of:

                (DocumentChunk, reranker_score)

            where the results are already ordered by
            descending reranker score.

        Returns
        -------
        bool
            True if the evidence is sufficient.
            False otherwise.
        """

        if not reranked_results:
            return False

        # --------------------------------------------------
        # Extract reranker scores
        # --------------------------------------------------

        scores = [
            float(score)
            for _, score in reranked_results
        ]

        if not scores:
            return False

        # --------------------------------------------------
        # Best score
        # --------------------------------------------------

        best_score = scores[0]

        # --------------------------------------------------
        # Average top 3
        # --------------------------------------------------

        top_3_scores = scores[:3]

        average_top_3 = (
            sum(top_3_scores) / len(top_3_scores)
            if top_3_scores
            else None
        )

        # --------------------------------------------------
        # Count results with score >= 2
        # --------------------------------------------------

        count_ge_2 = sum(
            1
            for score in scores
            if score >= 2.0
        )

        # --------------------------------------------------
        # Determine dominant section
        # --------------------------------------------------

        sections = [
            chunk.section_title
            for chunk, _ in reranked_results[:5]
            if chunk.section_title
        ]

        dominant_section_count = 0

        if sections:
            section_counts = {}

            for section in sections:
                section_counts[section] = (
                    section_counts.get(section, 0) + 1
                )

            dominant_section_count = max(
                section_counts.values()
            )

        # --------------------------------------------------
        # Apply evidence rules
        # --------------------------------------------------

        return EvidenceSufficiencyService.is_sufficient(
            best_score=best_score,
            average_top_3=average_top_3,
            count_ge_2=count_ge_2,
            dominant_section_count=dominant_section_count,
        )