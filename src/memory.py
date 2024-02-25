from utils.utils import *
from datetime import datetime
import re
import random
import numpy as np
from utils.utils import *
from sklearn.metrics.pairwise import cosine_similarity

class Memory:
    def __init__(self, kind, content, created_at, last_accessed_at, score=None,embedding=None, memories=[]):
        self.id = str(uuid.uuid4())
        self.kind = kind
        self.content = content
        self.created_at = created_at
        if not isinstance(last_accessed_at, str):
            print("last_accessed_at should be string timestamp format")
            self.last_accessed_at = unix_to_strftime(last_accessed_at)
            print(type(self.last_accessed_at))
        else:
            self.last_accessed_at = last_accessed_at
        #print(f"WTF {content} {type(created_at)} {type(last_accessed_at)}   ")
        #print(f"{type(LLM_IMPORTANCE)} {LLM_IMPORTANCE}")
        if LLM_IMPORTANCE == 0:
            self.importance = score
        else:
            self.importance = Memory.calculateImportanceScore(self.content, memories)

        self.recency_score = 1
        self.relevancy_score = 1
        self.overall_score = 1
        if embedding:
            self.embedding = embedding
        else:
            self.embedding = llm.embeddings(content)
        #self.simulation_id = simulation_id

        #session.add(self)
        #session.commit()
    def to_dict(self):
        return vars(self)

    def __str__(self, verbose=False):
        if verbose:
            return (
                f"Memory(c={self.content}, "
                f"t={self.kind}, "
                f"rel={self.relevancy_score}, "
                f"rec={self.recency_score}, "
                f"i={self.importance}, "
                f"o={self.overall_score}, "
                f"c_at={self.created_at}, "
                f"a_at={self.last_accessed_at})"
            )
        else:
            return self.content

    def calculateImportanceScore(content,previous_memories=[]):
        prompt = f'''
On the scale of 0 to 9, where 0 is purely mundane (e.g., brushing teeth, saw a bed) and 9 is extremely poignant (e.g., a break up, witnessed murder), rate the likely poignancy of the following  memory.

First give an explanation for your score.
Second, give your score as a single number do not include anything just one single number from 0 to 9
Answer with the format:
Explanation
score

Memory: {content}

Example input:
John sees a door
Example output:
People see doors everyday, this is mundane
0


        '''
        same_memory = None
        for mem in previous_memories:
            if mem.content == content:
                same_memory = mem
        if same_memory:
            pd("USING SAME_MEMORY CACHE")
            result = "{same_memory.importance}"
        else:
            result = llm.generate(prompt, "5")
        #cleaned_result = float(re.search(r'\d+', result).group() if re.search(r'\d+', result) else '5')
        try:
            cleaned_result = int(re.findall(r'\b\d+\b', result)[-1])
        except IndexError:
            cleaned_result = 5
        if cleaned_result > 9:
            cleaned_result = 9
        return cleaned_result

    def calculateRelevanceScore(memory_embedding, context_embedding):
        if context_embedding is None:
            return float(1)
        try:
            context_embedding = np.array(context_embedding)
            memory_embedding = np.array(memory_embedding)

            context_embedding = context_embedding.reshape(1, -1)
            memory_embedding = memory_embedding.reshape(1, -1)

            similarity = cosine_similarity(context_embedding, memory_embedding)[0][0]
            return float(similarity)
        except Exception as e:
            return float(0)

            similarity = cosine_similarity(context_embedding, memory_embedding)[0][0]
            return float(similarity)
        except Exception:
            return float(0)

    def calculateRecencyScore(last_accessed_at, time, decay=0.99):
        try:
            #print(f"laa {last_accessed_at} {type(last_accessed_at)}")
            #print(f"time {time} {type(time)}")
            last_accessed_at = int(datetime.strptime(last_accessed_at, "%Y-%m-%d %H:%M:%S").timestamp())
            time = int(datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp())
            return float(decay ** int(time - last_accessed_at))
        except OverflowError:
            return 0.0
