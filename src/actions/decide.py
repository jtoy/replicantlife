class DecideAction(Action):
    def execute(agent):
        llm_decide()
        if self.matrix.llm_action_flag == 1 and agent.kind != 'zombie':
            agent.llm_decide()
        else:
            agent.deterministic_decide()



    def llm_decide():
        agent = self
        unix_time = self.matrix.unix_time
        if agent.status == "dead":
            return agent

        # It is 12:00, time to make plans
        if unix_time % 86400 == 0 and self.matrix.allow_plan_flag == 1:
            agent.make_plans(unix_to_strftime(unix_time))

        # Recent memories importance > 100, time to reflect
        if self.matrix.allow_reflect_flag == 1 and agent.recent_memories_importance() > self.matrix.reflect_threshold:
            agent.reflect(unix_to_strftime(unix_time))

        if self.matrix.allow_meta_flag == 1 and random.randint(0,100) < 50:
            agent.evaluate_progress()

        agent.conversation_cooldown -= 1

        # In here, we double check first if agent's conversation messages depth > CONVERSATION_DEPTH
        # we will summarize it and then clear
        if agent.last_conversation is not None:
            if len(agent.last_conversation.messages) >= CONVERSATION_DEPTH:
                other_agent = agent.last_conversation.other_agent

                agent.summarize_conversation(unix_to_strftime(unix_time))
                other_agent.summarize_conversation(unix_to_strftime(unix_time))

                agent.conversation_cooldown = CONVERSATION_COOLDOWN
                other_agent.conversation_cooldown = CONVERSATION_COOLDOWN

        # In here, if agent is locked to a conversation, no need then to let them decide
        # we let them talk
        if agent.is_locked_to_convo():
            agent.talk({ "other_agents": [agent.last_conversation.other_agent], "timestamp": unix_to_strftime(unix_time) })
            return agent

        perceived_agents, perceived_locations, perceived_areas, perceived_objects = agent.perceive([a for a in self.matrix.agents if a != agent], self.matrix.environment, unix_to_strftime(unix_time))

        relevant_memories = agent.getMemories(agent.goal, unix_to_strftime(unix_time))
        relevant_memories_string = "\n".join(f"Memory {i + 1}:\n{memory}" for i, memory in enumerate(relevant_memories)) if relevant_memories else ""
        current_location = self.matrix.environment.get_location_from_coordinates(agent.x, agent.y)
        current_area = self.matrix.environment.get_area_from_coordinates(agent.x, agent.y)
        if agent.last_conversation is not None:
            relevant_memories_string += f"\n{agent} is currently in a conversation with {agent.last_conversation.other_agent}.\n"

        other_agents = [a for a in perceived_agents if a.status != "dead" and a.kind != "zombie"]

        #valid_actions = ["stay"]
        #example_strings = "\n\nExplanation: George will stay because it is still too early to go outside.\nAnswer: stay"
        valid_actions = []
        example_strings = "\n\n"
        agents_available_to_talk = []

        if "move" in agent.actions and not agent.is_locked_to_convo() and self.matrix.allow_movement == 1:
            # You can move, and have not decided where to move yet
            valid_actions.append("move <location>")
            example_strings = example_strings + "\n\nExplanation: George will move because he needs to be at the Park at 18:00.\nAnswer: move Park"

        if "continue_to_destination" in agent.actions and agent.current_destination is not None and not agent.is_locked_to_convo() and self.matrix.allow_movement == 1:
            # You can move, and have already decided where to move
            valid_actions.append("continue_to_destination")
            example_strings = example_strings + "\n\nExplanation: George will continue travelling to the Park because he wants to be there by 18:00.\nAnswer: continue_to_destination"
        if random.randint(0, 100) < 10 and self.allow_meta_flag == 1 and "meta_cognize" in agent.actions:
            valid_actions.append("meta_cognize")
            example_strings = example_strings + "\n\nExplanation: George will meta_cognize because he wants to improve its strategy towards his goal.\nAnswer: meta_cognize"

        if "talk" in agent.actions and not agent.is_locked_to_convo() and agent.conversation_cooldown <= 0:
            agents_available_to_talk = [a for a in other_agents if not a.is_locked_to_convo() and a.conversation_cooldown <= 0]
            if len(agents_available_to_talk) > 0:
                valid_actions.append("talk <person to talk to>")
                example_strings = example_strings + "\n\nExplanation: George will talk to Anne because he is trying to make new friends.\nAnswer: talk Anne"

        if "kill" in agent.actions and len(perceived_agents) > 0 and not agent.is_locked_to_convo():
            valid_actions.append("kill <person to kill>")
            example_strings = example_strings + "\n\nExplanation: George will kill Anne because no one else is around.\nAnswer: kill Anne"

        if len(valid_actions) == 0 and len(agent.destination_cache) > 0:
            interaction = f"{agent} is travelling to {self.environment.get_location_from_coordinates(agent.destination_cache[-1][0], agent.destination_cache[-1][1]).name}"
            print_and_log(interaction, f"{self.id}:events:{agent.name}")
            agent.move()
            return agent
        if mem:
            objects = mem
        else:
            objects = [obj.name.lower() for obj in perceived_objects] + [a.name.lower() for a in perceived_agents if a.kind != "human"],

        variables = {
            "selfContext": agent.getSelfContext(),
            "relevant_memories": relevant_memories_string,
            "agent": agent,
            "other_agents": [a.name for a in other_agents],
            "agents_available_to_talk": [a.name for a in agents_available_to_talk],
            'objects': objects,
            'examples': example_strings,
            'actions': valid_actions,
            'location': current_location.name if current_location is not None else "",
            'area': current_area if current_area is not None else "",
            'spatial_memory': [loc.name for loc in agent.spatial_memory],
            'time': unix_to_strftime(unix_time)
        }

        msg = llm.prompt("decide", variables)
        match = re.search(r"Answer:\s*(.+)", msg)
        explanation_match = re.search(r"Explanation:\s*(.+)", msg)
        explanation = explanation_match.group(1) if explanation_match else None

        msg = match.group(1) if match else None

        if msg is None:
            return "stay", ""

        decision, parameters = msg.split(" ", 1) + [""] * (1 - msg.count(" "))

        if decision == "talk":
            if len(agents_available_to_talk) > 0:
                agent.talk({ "target": parameters, "other_agents": agents_available_to_talk, "timestamp": unix_to_strftime(unix_time) })
                self.conversation_counter += 1
        elif decision == "move":
            agent.move({ "target": parameters, "environment": self.matrix.environment })
        elif decision == "continue_to_destination":
            if agent.current_destination is not None:
                agent.move({ "environment": self.environment })
        elif decision == "meta_cognize":
            agent.meta_cognize(unix_to_strftime(unix_time),True)
        elif decision == "kill":
            if len(other_agents) > 0:
                target = find_most_similar(parameters, [a.name for a in other_agents])
                for a in other_agents:
                    if target == a.name:
                        agent.kill(a, unix_to_strftime(unix_time))
                        if a.status == "dead":
                            witnesses = (set(perceived_agents) - {a})
                            for witness in witnesses:
                                witness.addMemory("perceived", f"{a} was murdered by {agent} at {self.environment.get_area_from_coordinates(a.x, a.y)} {self.environment.get_location_from_coordinates(a.x, a.y)}", unix_to_strftime(unix_time), 9)

        memory = agent.addMemory("decision",f"I decided to {decision} because {explanation}",unix_to_strftime(unix_time),random.randint(1,4))
        if memory and memory.importance >= 6:
            agent.update_goals()
        return agent
