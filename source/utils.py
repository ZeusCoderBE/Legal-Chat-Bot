def find_relevant_contexts(contexts, answers):
    lst_Relevant_Documents = []
    for answer in answers:
        for context in contexts:
            if answer in context and context not in lst_Relevant_Documents:
                lst_Relevant_Documents.append(context)
    return lst_Relevant_Documents
