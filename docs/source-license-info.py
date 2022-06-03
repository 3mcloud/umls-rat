"""
See https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf for basic UMLS license aggreement.
"""
import argparse
import itertools
import logging
import os
import sys
import textwrap

from umlsrat.api.metathesaurus import MetaThesaurus

logger = logging.getLogger(os.path.basename(__file__))

RESTRICTION_LEVELS = {
    0: """License Agreement for Use of the UMLS® Metathesaurus®
This Agreement is made by and between the National Library of Medicine, Department of Health and Human Services (hereinafter referred to as "NLM") and the LICENSEE.
WHEREAS, the NLM was established by statute in order to assist the advancement of medical and related sciences, and to aid the dissemination and exchange of scientific and other information important to the progress of medicine and to the public health (section 465 of the Public Health Service Act, as amended (42 U.S.C. section 286)), and to carry out this purpose has been authorized to develop the Unified Medical Language System® (UMLS) to facilitate the retrieval and integration of machine-readable biomedical information from disparate sources;
WHEREAS, the NLM's UMLS project has produced the UMLS Metathesaurus, a machine-readable vocabulary knowledge source, that is useful in a variety of settings;
WHEREAS, the LICENSEE is willing to use the UMLS Metathesaurus at its sole risk and at no expense to NLM, which will result in information useful to NLM, may provide immediate improvements in biomedical information transfer to segments of the biomedical community, and is consistent with NLM's statutory functions,
NOW THEREFORE, it is mutually agreed as follows:
1. The NLM hereby grants a nonexclusive, non-transferable right to LICENSEE to use the UMLS Metathesaurus and incorporate its content in any computer applications or systems designed to improve access to biomedical information of any type subject to the restrictions in other provisions of this Agreement. The names and addresses of licensees authorized to use the UMLS products are public information.
2. No charges, usage fees, or royalties will be paid to NLM.
3. LICENSEE is prohibited from distributing the UMLS Metathesaurus or subsets of it, including individual vocabulary sources within the Metathesaurus, except (a) as an integral part of computer applications developed by LICENSEE for a purpose other than redistribution of vocabulary sources contained in the UMLS Metathesaurus and (b) if permitted by paragraph 12 of this agreement.
4. LICENSEE agrees to inform NLM prior to distributing any application(s) in which it is using the UMLS Metathesaurus and is encouraged to inform NLM of any difficulties encountered in using the UMLS Metathesaurus, and changes or enhancements to the UMLS Metathesaurus that would make it more useful to LICENSEE and its user groups.
5. Within 30 days of the end of any calendar year in which LICENSEE makes use of the UMLS Metathesaurus, LICENSEE agrees to provide NLM with a brief report on the usefulness of the UMLS Metathesaurus in general and, if applicable, on the usefulness of CPT in the UMLS format in particular. LICENSEE is strongly encouraged to submit to NLM locally developed extensions to the UMLS Metathesaurus that are potentially useful to other UMLS users for consideration for potential inclusion in the UMLS Metathesaurus.
6. NLM represents that the data provided under this Agreement were formatted with a reasonable standard of care, but makes no warranties express or implied, including no warranty of merchantability or fitness for particular purpose, regarding the accuracy or completeness of the data or that the machine-readable copy is error free. Therefore, LICENSEE agrees to hold NLM, the Government, and any organization contributing a vocabulary
source to the UMLS Metathesaurus free from any liability resulting from errors in terminology or other data or on the machine-readable copy. NLM and such other organizations disclaim any liability for any consequences due to use, misuse, or interpretation of information contained or not contained in the UMLS Metathesaurus.
7. NLM represents that its ability to continue to include certain vocabulary sources within the UMLS Metathesaurus is dependent on continuing contractual relations or agreements with the copyright holders for these vocabulary sources. Therefore, LICENSEE agrees to hold NLM and the individual copyright holder free from any liability resulting from the removal of any vocabulary source from future editions of the UMLS Metathesaurus.
8. NLM reserves the right to change the type and format of its machine-readable data. NLM agrees to inform LICENSEE of any changes to the format of the UMLS Metathesaurus, EXCEPT the addition of entirely new data elements to the Metathesaurus, at least 90 days before the data are distributed.
9. The presence in the UMLS Metathesaurus of vocabulary or data produced by organizations other than NLM does not imply any endorsement of the UMLS Metathesaurus by these organizations.
10. LICENSEE shall acknowledge NLM as its source of the UMLS Metathesaurus, citing the year and version number, in a suitable and customary manner but may not in any way indicate or imply that NLM or any of the organizations whose vocabulary sources are included in the UMLS has endorsed LICENSEE or its products.
11. Some of the Material in the UMLS Metathesaurus is from copyrighted sources. If LICENSEE uses any material from copyrighted sources from the UMLS Metathesaurus:
    a) the LICENSEE is required to display in full, prior to providing user access to the Metathesaurus or any of the vocabulary sources within the UMLS, the following wording in order that its users be made aware of these copyright constraints:
"Some material in the UMLS Metathesaurus is from copyrighted sources of the respective copyright holders. Users of the UMLS Metathesaurus are solely responsible for compliance with any copyright, patent or trademark restrictions and are referred to the copyright, patent or trademark notices appearing in the original sources, all of which are hereby incorporated by reference.";
to display a list of all of the vocabularies contained within the UMLS Metathesaurus that are used in the LICENSEE's application; and to indicate for each vocabulary any appropriate copyright notice and whether the entire contents are present or only a portion of it.
    b) the LICENSEE is prohibited from altering UMLS and other vocabulary source content contained within the UMLS Metathesaurus, but may include content from other sources in applications that also contain content from the UMLS Metathesaurus. The LICENSEE may not imply in any way that data from other sources is part of the UMLS Metathesaurus or of any of its vocabulary sources.
    c) the LICENSEE is required to include in its applications identifiers from the UMLS Metathesaurus such that the original source vocabularies for any data obtained from the UMLS Metathesaurus can be determined by reference to a complete version of the UMLS Metathesaurus.
12. For material in the UMLS Metathesaurus obtained from some sources additional restrictions on LICENSEE's use may apply. The categories of additional restrictions are described below. The list of UMLS Metathesaurus Vocabulary Sources, which is part of this Agreement and is updated when each version of the Metathesaurus is released, indicates the category of additional restrictions, if any, that apply to each vocabulary source.
LICENSEE should contact the copyright holder directly to discuss uses of a source vocabulary beyond those allowed under this license agreement. If LICENSEE or LICENSEE's end user has a separate agreement with the copyright holder for use of a UMLS Metathesaurus source vocabulary, LICENSEE or LICENSEE's end user may use vocabulary source content obtained from the UMLS Metathesaurus in accordance with the terms of the separate agreement.""",
    1: """12.1. Category 1:
LICENSEE is prohibited from translating the vocabulary source into another language or from producing other derivative works based on this single vocabulary source.

""",
    2: """12.2. Category 2:
    All category 1 restrictions AND LICENSEE is prohibited from using the vocabulary source in operational applications that create records or information containing data from the vocabulary source. Use for data creation research or product development is allowed.""",
    3: """12.3. Category 3:
    LICENSEE's right to use material from the source vocabulary is restricted to internal use at the LICENSEE's site(s) for research, product development, and statistical analysis only. Internal use includes use by employees, faculty, and students of a single institution at multiple sites. Notwithstanding the foregoing, use by students is limited to doing research under the direct supervision of faculty. Internal research, product development, and statistical analysis use expressly excludes: use of material from these copyrighted sources in routine patient data creation; incorporation of material from these copyrighted sources in any publicly accessible computer-based information system or public electronic bulletin board including the Internet; publishing or translating or creating derivative works from material from these copyrighted sources; selling, leasing, licensing, or otherwise making available material from these copyrighted works to any unauthorized party; and copying for any purpose except for back up or archival purposes.
    
    LICENSEE may be required to display special copyright, patent and/or trademark notices before displaying content from the vocabulary source. Applicable notices are included in the list of UMLS Metathesaurus Vocabulary sources, that is part of this Agreement.

""",
    4: """12.4. Category 4:
    12.4.1. LICENSEE is prohibited from translating the vocabulary source into another language or from altering the vocabulary source content.
    
    12.4.2. LICENSEE's right to use the vocabulary source is restricted to use in the U.S. by LICENSEE's employees, contractors, faculty, students, clients, patients, or constituents within electronic systems or devices built, purchased, licensed, or used by LICENSEE for U.S. governmental purposes or for any health care, public health, research, educational, or statistical use in the U.S. Use by students is limited to research or educational activities under the direct supervision of faculty.
    
    12.4.3. LICENSEE has the right to distribute the vocabulary source in the U.S., but only in combination with other UMLS Metathesaurus content. Further, LICENSEE's right to distribute is restricted to:
    
    Electronic distribution to LICENSEE's direct U.S. affiliates, or to other U.S. entities that have signed the UMLS license, in order to facilitate use of the vocabulary for health care, public health, research, educational or statistical purposes in the U.S. only.
    LICENSEE must take reasonable precautions to prevent distribution of the vocabulary source to non-US entities.
    LICENSEE must include in its annual report a list of all U.S. affiliates or other U.S. entities to whom it has distributed content from the vocabulary source.
    Distribution of encoded patient level data sets or knowledge encoded in the vocabulary source by LICENSEE to any U.S. entity for use in the U.S. only.
    Inclusion of encoded records or content from the vocabulary source in: (1) free publicly accessible retrieval systems or (2) fee-based retrieval systems that are accessible within the U.S. only, provided that these systems do not permit users to copy or extract any significant portion of the vocabulary source.
    
    12.4.4. DEFINITIONS
        a. U.S. is defined as all U.S. states, territories, and the District of Columbia; any U.S. government facility or office, whether permanent or temporary, wherever located; and access to a system in any of these locations by U.S. government employees, designated representatives or contractors, wherever located, for U.S. government purposes.
        b. U.S. entity is defined as (i) for government entities, an agency or department of the U.S. Government, (ii) for corporations, as a corporation incorporated and operating in the U.S.; and (iii) for other entities as an entity organized under the laws of the U.S.""",
    9: """Category 9: 
    SNOMED CT® AFFILIATE LICENSE AGREEMENT""",
}


def wrap(text):
    return "\n".join(textwrap.fill(line, width=70) for line in text.split("\n"))


def rlevel_details() -> str:
    rlevel_text = "\n\n".join(
        wrap(RESTRICTION_LEVELS[l]) for l in sorted(RESTRICTION_LEVELS.keys())
    )

    rlevel_text = textwrap.indent(rlevel_text, "      ")

    return "Details\n" "=======\n" "::\n\n" + rlevel_text + "\n"


def main():
    parser = argparse.ArgumentParser()

    MetaThesaurus.add_args(parser)

    parser.add_argument(
        "--out-file",
        help="Write RST output to this file.",
        type=str,
        default="source-licenses.rst",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    api = MetaThesaurus.from_namespace(args)

    rst_string = (
        "***************\n"
        "Source Licenses\n"
        "***************\n"
        f"Information regarding licensing of the sources contained in UMLS version {api.umls_version}. "
        f"`Basic UMLS License Agreement <https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf>`_ "
        f"has been copied under `details`_\n"
        "\n"
    )

    def get_rlevel(obj):
        return obj.get("restrictionLevel")

    all_source_info = sorted(api.source_metadata_index.values(), key=get_rlevel)
    for rlevel, group in itertools.groupby(all_source_info, key=get_rlevel):
        rst_string += f"\n" f"CATEGORY {rlevel}\n"
        rst_string += "==========\n\n"

        for info in sorted(group, key=lambda _: _["shortName"]):
            text = f"{info['shortName']} ({info['abbreviation']})"
            rst_string += f"  * {text}\n"

    rst_string += "\n\n" + rlevel_details()
    # print(rst_string)

    out_file = args.out_file
    with open(out_file, "w", encoding="utf-8") as ofp:
        print(rst_string, file=ofp)


if __name__ == "__main__":
    sys.exit(main())
