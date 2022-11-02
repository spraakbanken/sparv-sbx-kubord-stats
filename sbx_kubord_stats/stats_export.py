"""Sparv exporter which generats word frequency files for the Kubord project."""

from collections import defaultdict

from sparv.api import (AllSourceFilenames, Annotation, AnnotationAllSourceFiles, Config, Export,
                       ExportAnnotationsAllSourceFiles, SourceAnnotationsAllSourceFiles, exporter, get_logger, util)
from sparv.modules.stats_export.stats_export import write_csv

logger = get_logger(__name__)


@exporter("Kubord 2 word frequency list", language=["swe"])
def freq_list_kubord(
    source_files: AllSourceFilenames = AllSourceFilenames(),
    word: AnnotationAllSourceFiles = AnnotationAllSourceFiles("<token:word>"),
    token: AnnotationAllSourceFiles = AnnotationAllSourceFiles("<token>"),
    dephead_ref: AnnotationAllSourceFiles = AnnotationAllSourceFiles("<token:dephead_ref>"),
    deprel: AnnotationAllSourceFiles = AnnotationAllSourceFiles("<token:deprel>"),
    sentence_id: AnnotationAllSourceFiles = AnnotationAllSourceFiles("<sentence>:misc.id"),
    annotations: ExportAnnotationsAllSourceFiles = ExportAnnotationsAllSourceFiles("stats_export.annotations"),
    source_annotations: SourceAnnotationsAllSourceFiles = SourceAnnotationsAllSourceFiles("stats_export.source_annotations"),
    remove_namespaces: bool = Config("export.remove_module_namespaces", True),
    sparv_namespace: str = Config("export.sparv_namespace"),
    source_namespace: str = Config("export.source_namespace"),
    out: Export = Export("sbx_kubord_stats.frequency_list/stats_[metadata.id].csv"),
    delimiter: str = Config("stats_export.delimiter"),
    cutoff: int = Config("stats_export.cutoff")):
    """Create a word frequency list with bigrams of dependency relations."""
    logger.progress(total=len(source_files) + 1)

    # Get annotations list and export names
    annotation_list, token_attributes, export_names = util.export.get_annotation_names(
        annotations, source_annotations or [], source_files=source_files, token_name=token.name,
        remove_namespaces=remove_namespaces, sparv_namespace=sparv_namespace, source_namespace=source_namespace)

    # Get all token and struct annotations (except the span annotations)
    token_annotations = [a for a in annotation_list if a.attribute_name in token_attributes]
    struct_annotations = [a for a in annotation_list if ":" in a.name and a.attribute_name not in token_attributes]

    # Calculate token frequencies
    freq_dict = defaultdict(int)
    for source_file in source_files:

        # Get values for struct annotations (per token)
        struct_values = []
        for struct_annotation in struct_annotations:
            struct_annot = Annotation(struct_annotation.name, source_file=source_file)
            token_parents = Annotation(token.name, source_file=source_file).get_parents(struct_annot)
            try:
                struct_annot_list = list(struct_annot.read())
                struct_values.append([struct_annot_list[p] if p is not None else "" for p in token_parents])
            # Handle cases where some source files are missing structural source annotations
            except FileNotFoundError:
                struct_values.append(["" for _ in token_parents])

        # Read sentences
        sentence_id_annot = Annotation(sentence_id.name, source_file=source_file)
        sentence_ids = sentence_id_annot.read()
        sentence_tokens, _ = sentence_id_annot.get_children(word)

        tokens = list(word.read_attributes(source_file, token_annotations))
        dep_info = list(word.read_attributes(source_file, [dephead_ref, deprel]))
        no_attrs = len(tokens[0]) - 1

        for _sentid, sent in zip(sentence_ids, sentence_tokens):
            for token_index in sent:
                structs_tuple = tuple([struct[token_index] for struct in struct_values])
                token1 = list(tokens[token_index])
                token_dh, token_dr = dep_info[token_index]
                dephead_index = sent[int(token_dh) - 1] if token_dh else None
                if dephead_index:
                    token2 = list(tokens[dephead_index])
                    token_list = [token1[0], token2[0], token_dr, *token1[1:], *token2[1:], *structs_tuple]
                else:
                    token_list = [token1[0], "-", token_dr, *token1[1:], *["-"] * no_attrs, *structs_tuple]

                freq_dict[tuple(token_list)] += 1
        logger.progress()

    # Create header
    struct_names = [export_names.get(a.annotation_name, a.annotation_name) + ":" + export_names[a.name]
                           for a in struct_annotations]
    token1_names = [(export_names[a.name]) + " 1" for a in token_annotations[1:]]
    token2_names = [(export_names[a.name]) + " 2" for a in token_annotations[1:]]
    column_names = ["word 1", "word 2", "relation"] + token1_names + token2_names + struct_names + ["count"]

    write_csv(out, column_names, freq_dict, delimiter, cutoff)
    logger.progress()
