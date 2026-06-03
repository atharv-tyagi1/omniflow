from typing import List


class RecursiveCharacterTextSplitter:
    """
    Recursively splits text by decreasing order of semantic boundaries
    (paragraphs, sentences, words, characters) to ensure chunks remain
    under a specific character limit while maintaining contextual continuity.
    """

    def __init__(
        self,
        separators: List[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self._separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        final_chunks = []

        separator = self._separators[-1]
        for _s in self._separators:
            if _s == "":
                separator = _s
                break
            if _s in text:
                separator = _s
                break

        splits = text.split(separator) if separator else list(text)

        good_splits = []
        _separator = "" if separator == "" else separator

        for s in splits:
            if len(s) < self._chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged = self._merge_splits(good_splits, _separator)
                    final_chunks.extend(merged)
                    good_splits = []

                # If a single split is still larger than chunk_size, we recurse on it.
                other_info = self.split_text(s)
                final_chunks.extend(other_info)

        if good_splits:
            merged = self._merge_splits(good_splits, _separator)
            final_chunks.extend(merged)

        return final_chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        # Simple merging algorithm respecting chunk_size and chunk_overlap
        docs = []
        current_doc = []
        total = 0

        for d in splits:
            _len = len(d)
            if (
                total + _len + (len(separator) if len(current_doc) > 0 else 0)
                > self._chunk_size
            ):
                if total > 0:
                    docs.append(separator.join(current_doc))

                    # Backtrack to satisfy overlap
                    while total > self._chunk_overlap or (
                        total + _len + (len(separator) if len(current_doc) > 0 else 0)
                        > self._chunk_size
                        and total > 0
                    ):
                        total -= len(current_doc[0]) + (
                            len(separator) if len(current_doc) > 1 else 0
                        )
                        current_doc.pop(0)

            current_doc.append(d)
            total += _len + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            docs.append(separator.join(current_doc))

        return docs
