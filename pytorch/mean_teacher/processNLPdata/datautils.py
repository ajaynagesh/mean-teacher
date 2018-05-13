#!/usr/bin/env python

import numpy as np
from collections import defaultdict
import re

class Datautils:

    ## read the data from the file with the entity_ids provided by entity_vocab and context_ids provided by context_vocab
    ## data format:
    #################
    ## [label]\t[Entity Mention]\t[[context mention1]\t[context mention2],\t...[]]
    ## NOTE: The label to be removed later from the dataset and the routine suitably adjusted. Inserted here for debugging

    @classmethod
    def read_data(cls, filename, entity_vocab, context_vocab):
        labels = []
        entities = []
        contexts = []

        with open(filename) as f:
            word_counts = dict()
            for line in f:
                vals = line.strip().split('\t')
                labels.append(vals[0].strip())
                if vals[1] not in word_counts:
                    word_counts[vals[1]] = 1
                else:
                    word_counts[vals[1]] += 1
                word_id = entity_vocab.get_id(vals[1])
                if word_id is not None:
                    entities.append(word_id)
                contexts.append([context_vocab.get_id(c) for c in vals[2:] if context_vocab.get_id(c) is not None])

            num_count_words = 0
            for word in word_counts:
                if word_counts[word] >= 6:
                    num_count_words+=1
            print('num count words:',num_count_words)

        # return np.array(entities), np.array([np.array(c) for c in contexts]), np.array(labels)
        return entities, contexts, labels

    @classmethod
    def read_re_data(cls, filename, type, max_entity_len, max_inbetween_len):
        labels = []
        entities1 = []
        entities2 = []
        chunks_inbetween = []
        word_counts = dict()

        with open(filename) as f:
            for line in f:
                vals = line.strip().split('\t')

                sentence_str = ' ' + vals[5].strip()
                entity1 = vals[2].strip()
                entity2 = vals[3].strip()
                entities1_words = entity1.strip().split('_')
                entities2_words = entity2.strip().split('_')

                entity1_pattern = entity1.replace('(', "\(")
                entity1_pattern = entity1_pattern.replace(')', "\)")
                entity1_pattern = entity1_pattern.replace('[', "\[")
                entity1_pattern = entity1_pattern.replace(']', "\]")
                entity1_pattern = entity1_pattern.replace('{', "\{")
                entity1_pattern = entity1_pattern.replace('}', "\}")
                entity1_pattern = entity1_pattern.replace('"', '\\"')

                entity2_pattern = entity2.replace('(', "\(")
                entity2_pattern = entity2_pattern.replace(')', "\)")
                entity2_pattern = entity2_pattern.replace('[', "\[")
                entity2_pattern = entity2_pattern.replace(']', "\]")
                entity2_pattern = entity2_pattern.replace('{', "\{")
                entity2_pattern = entity2_pattern.replace('}', "\}")
                entity2_pattern = entity2_pattern.replace('"', '\\"')

                entity1_idxs = [m.start() for m in re.finditer(' ' + entity1_pattern + ' ', sentence_str)]
                entity2_idxs = [m.start() for m in re.finditer(' ' + entity2_pattern + ' ', sentence_str)]

                if len(entity1_idxs) == 0:
                    entity1_idxs = [m.start() for m in re.finditer(entity1_pattern, sentence_str)]

                if len(entity2_idxs) == 0:
                    entity2_idxs = [m.start() for m in re.finditer(entity2_pattern, sentence_str)]

                # this happens when not all words of entity are all connected by '_' in sentence
                # e.g.: m.03h64	m.01ky9c	hong_kong	hong_kong_international_airport	/location/location/contains	turbo jet ferries depart from the hong_kong macao ferry terminal , sheung wan , the hong_kong china ferry terminal in kowloon and cross boundary passenger ferry terminal at hong_kong international airport . ###END###
                if len(entity1_idxs) == 0:
                    sentence_str_tab = sentence_str.replace(' ', "_")
                    entity1_idxs = [m.start() for m in re.finditer('_' + entity1_pattern + '_', sentence_str_tab)]
                if len(entity2_idxs) == 0:
                    sentence_str_tab = sentence_str.replace(' ', "_")
                    entity2_idxs = [m.start() for m in re.finditer('_' + entity2_pattern + '_', sentence_str_tab)]

                if len(entity1_idxs) > 0 and len(entity2_idxs) > 0:
                    # initial the shortest distance between two entities as some big num, such as 2000
                    d_abs = 2000   #todo: replace with constant max of system

                    entity1_idx = entity1_idxs[0]  # entity can appear more than once in sentence
                    entity2_idx = entity2_idxs[0]
                    for idx1 in entity1_idxs:
                        for idx2 in entity2_idxs:
                            if abs(idx1-idx2) < d_abs and idx1 != idx2:
                                d_abs = abs(idx1-idx2)
                                entity1_idx = idx1
                                entity2_idx = idx2

                    if entity1_idx < entity2_idx:
                        sentence_str_1 = sentence_str[:entity1_idx] + ' @entity ' + sentence_str[entity1_idx+len(entity1)+2:entity2_idx]
                        sentence_str_2 = ' @entity ' + sentence_str[entity2_idx+len(entity2)+2:]
                        sentence_str = sentence_str_1 + ' ' + sentence_str_2

                    elif entity1_idx > entity2_idx:
                        sentence_str_1 = sentence_str[:entity2_idx] + ' @entity ' + sentence_str[entity2_idx + len(entity2)+2:entity1_idx]
                        sentence_str_2 = ' @entity ' + sentence_str[entity1_idx+len(entity1)+2:]
                        sentence_str = sentence_str_1 + ' ' + sentence_str_2

                    sentence_str = sentence_str.lower()
                    sentence_str = sentence_str.replace('-lrb-', " ( ")
                    sentence_str = sentence_str.replace('-rrb-', " ) ")
                    sentence_str = ' '.join(sentence_str.split())
                    inbetween_str = sentence_str.partition("@entity")[2].partition("@entity")[0]

                    # sentences_words = re.split( r'(\\n| |#|%|\'|\"|,|:|-|_|;|!|=|\.|\(|\)|\$|\?|\*|\+|\]|\[|\{|\}|\\|\/|\||\<|\>|\^|\`|\~)',sentence_str)[:-14]  # the last 14 character are "###END###"
                    inbetween_words = re.split(r'(\\n| |#|%|\'|\"|,|:|-|_|;|!|=|\(|\)|\$|\?|\*|\+|\]|\[|\{|\}|\\|\/|\||\<|\>|\^|\`|\~)',inbetween_str)

                    # i = 0
                    # while i < len(sentences_words):
                    #     word = sentences_words[i]
                    #
                    #     if len(word) == 0 or word is ' ':
                    #         sentences_words.remove(word)
                    #         i -= 1
                    #     elif word[0] is not '@' and '@' in word:
                    #         sentences_words[i] = '@email'
                    #     elif word[0] is not '@' and not word.isalnum() and len(word) > 1 and '&' not in word:
                    #         print(word)
                    #
                    #     i += 1

                    i = 0
                    while i < len(inbetween_words):
                        word = inbetween_words[i]

                        if len(word) == 0 or word is ' ':
                            inbetween_words.remove(word)
                            i -= 1
                        elif word[0] is not '@' and '@' in word:
                            inbetween_words[i] = '@email'
                        elif word[:3] is 'www':
                            inbetween_words[i] = '@web'

                        i += 1

                    if len(inbetween_words) <= max_inbetween_len or type is not 'train':   # when max_inbetween_len = 60, filter out 2464 noise

                        labels.append(vals[4])

                        #fan: should we swap entities1_words and entities2_words, if entity1_idx > entity2_idx?


                        if len(entities1_words) > max_entity_len:
                            entities1_words = entities1_words[:max_entity_len]
                        if len(entities2_words) > max_entity_len:
                            entities2_words = entities2_words[:max_entity_len]

                        for word in inbetween_words:
                            if word not in word_counts:
                                word_counts[word] = 1
                            else:
                                word_counts[word] += 1

                        for word in entities1_words:
                            if word not in word_counts:
                                word_counts[word] = 1
                            else:
                                word_counts[word] += 1

                        for word in entities2_words:
                            if word not in word_counts:
                                word_counts[word] = 1
                            else:
                                word_counts[word] += 1

                        entities1.append(entities1_words)
                        entities2.append(entities2_words)
                        chunks_inbetween.append(inbetween_words)
                else:
                    assert False, line

        return entities1, entities2, labels, chunks_inbetween, word_counts

    ## Takes as input an array of entity mentions(ids) along with their contexts(ids) and converts them to individual pairs of entity and context
    ## Entity_Mention_1  -- context_mention_1, context_mention_2, ...
    ## ==>
    ## Entity_Mention_1 context_mention_1 0 ## Note the last number is the mention id, needed later to associate entity mention with all its contexts
    ## Entity_Mention_1 context_mention_2 1
    ## ....

    @classmethod
    def prepare_for_skipgram(cls, entities, contexts):

        entity_ids = []
        context_ids = []
        mention_ids = []
        for i in range(len(entities)):
            word = entities[i]
            context = contexts[i]
            for c in context:
                entity_ids.append(word)
                context_ids.append(c)
                mention_ids.append(i)
        return np.array(entity_ids), np.array(context_ids), np.array(mention_ids)


    ## NOTE: To understand the current negative sampling and replace it with a more simpler version. Keeping it as it is now.
    @classmethod
    def collect_negatives(cls, entities_for_sg, contexts_for_sg, entity_vocab, context_vocab):

        n_entities = entity_vocab.size()
        n_contexts = context_vocab.size()
        negatives = np.empty((n_entities, n_contexts))

        for i in range(n_entities):
            negatives[i,:] = np.arange(n_contexts)
        negatives[entities_for_sg, contexts_for_sg] = 0
        return negatives

    @classmethod
    def construct_indices(cls, mentions, contexts):

        entityToPatternsIdx = defaultdict(set)
        for men, ctxs in zip(list(mentions), list([list(c) for c in contexts])):
            for ctx in ctxs:
                tmp = entityToPatternsIdx[men]
                tmp.add(ctx)
                entityToPatternsIdx[men] = tmp

        patternToEntitiesIdx = defaultdict(set)
        for men, ctxs in zip(list(mentions), list([list(c) for c in contexts])):
            for ctx in ctxs:
                tmp = patternToEntitiesIdx[ctx]
                tmp.add(men)
                patternToEntitiesIdx[ctx] = tmp

        return entityToPatternsIdx, patternToEntitiesIdx
