"""Tabular QL agent"""
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import framework
import utils

DEBUG = False

GAMMA = 0.5  # discounted factor
TRAINING_EP = 0.5  # epsilon-greedy parameter for training
TESTING_EP = 0.05  # epsilon-greedy parameter for testing
NUM_RUNS = 10
NUM_EPOCHS = 2000
NUM_EPIS_TRAIN = 25  # number of episodes for training at each epoch
NUM_EPIS_TEST = 50  # number of episodes for testing
ALPHA = 0.001  # learning rate for training

ACTIONS = framework.get_actions()
OBJECTS = framework.get_objects()
NUM_ACTIONS = len(ACTIONS)
NUM_OBJECTS = len(OBJECTS)


# pragma: coderesponse template
def epsilon_greedy(state_1, state_2, q_func, epsilon):
    """Returns an action selected by an epsilon-Greedy exploration policy

    Args:
        state_1, state_2 (int, int): two indices describing the current state
        q_func (np.ndarray): current Q-function
        epsilon (float): the probability of choosing a random command

    Returns:
        (int, int): the indices describing the action/object to take
    """
    if np.random.random() <= epsilon:
        action_index = np.random.randint(0, NUM_ACTIONS)
        object_index = np.random.randint(0, NUM_OBJECTS)

    else:
        action_index = np.argmax(np.max(q_func[state_1, state_2, :, :], axis=1))
        object_index = np.argmax(q_func[state_1, state_2, :, :][action_index])
        # action_to_take = np.argmax(q_func[state_1, state_2, :, :])
        # print("action to take: " + str(action_to_take))
        # action_index, object_index = action_to_take[2], action_to_take[3]

    return (action_index, object_index)


# pragma: coderesponse end


# pragma: coderesponse template
def tabular_q_learning(q_func, current_state_1, current_state_2, action_index,
                       object_index, reward, next_state_1, next_state_2,
                       terminal):
    """Update q_func for a given transition

    Args:
        q_func (np.ndarray): current Q-function
        current_state_1, current_state_2 (int, int): two indices describing the current state
        action_index (int): index of the current action
        object_index (int): index of the current object
        reward (float): the immediate reward the agent recieves from playing current command
        next_state_1, next_state_2 (int, int): two indices describing the next state
        terminal (bool): True if this episode is over

    Returns:
        None
    """
    if not terminal:
        current_Q = q_func[current_state_1, current_state_2, action_index,
            object_index]
        # print(next_state_1)
        # print(next_state_2)
        # print(object_index)
        next_V = np.max(q_func[next_state_1, next_state_2, :,
            :])

        # Update Q
        q_func[current_state_1, current_state_2, action_index,
            object_index] = (1 - ALPHA) * current_Q + ALPHA * (reward + GAMMA * next_V)


    return None  # This function shouldn't return anything


# pragma: coderesponse end


# pragma: coderesponse template
def run_episode(for_training):
    """ Runs one episode
    If for training, update Q function
    If for testing, computes and return cumulative discounted reward

    Args:
        for_training (bool): True if for training

    Returns:
        None
    """
    epsilon = TRAINING_EP if for_training else TESTING_EP
    gamma_step = 1
    epi_reward = 0

    # Game initialization:

    (current_room_desc, current_quest_desc, terminal) = framework.newGame()

    while not terminal:
        # Choose next action and execute

        current_room_desc_index = dict_room_desc[current_room_desc]
        current_quest_desc_index = dict_quest_desc[current_quest_desc]

        action_to_take_index, object_to_take_index = epsilon_greedy(current_room_desc_index, current_quest_desc_index, q_func, epsilon)
        next_room_desc, next_quest_desc, reward, new_terminal = framework.step_game(current_room_desc, current_quest_desc, action_to_take_index, object_to_take_index)

        # In Course Terminal was instantly updated to new_terminal

        next_room_desc_index = dict_room_desc[next_room_desc]
        next_quest_desc_index = dict_quest_desc[next_quest_desc]

        if for_training:
            # update Q-function.
            tabular_q_learning(q_func, current_room_desc_index, current_quest_desc_index, action_to_take_index, object_to_take_index, reward, next_room_desc_index, next_quest_desc_index, terminal)
            pass

        if not for_training:
            # update reward
            #epi_reward = epi_reward + reward
            epi_reward = epi_reward + gamma_step * reward
            gamma_step *= GAMMA
            # In Course was: epi_reward + gamma^step * reward
            pass


        # prepare next step
        terminal = new_terminal

        # if terminal and not for_training:
        #     print("Terminal Q-Value: " + str(np.max(q_func[current_room_desc_index, current_quest_desc_index, :, :])))
        #     print("Terminal Reward: " + str(reward))
        #     print("Episod Reward: " + str(epi_reward))


        current_room_desc = next_room_desc
        current_quest_desc = next_quest_desc

        

            

    if not for_training:
        return epi_reward


# pragma: coderesponse end


def run_epoch():
    """Runs one epoch and returns reward averaged over test episodes"""
    rewards = []

    for _ in range(NUM_EPIS_TRAIN):
        run_episode(for_training=True)

    for _ in range(NUM_EPIS_TEST):
        rewards.append(run_episode(for_training=False))

    return np.mean(np.array(rewards))


def run():
    """Returns array of test reward per epoch for one run"""
    global q_func
    q_func = np.zeros((NUM_ROOM_DESC, NUM_QUESTS, NUM_ACTIONS, NUM_OBJECTS))

    single_run_epoch_rewards_test = []
    pbar = tqdm(range(NUM_EPOCHS), ncols=80)
    for _ in pbar:
        single_run_epoch_rewards_test.append(run_epoch())
        pbar.set_description(
            "Avg reward: {:0.6f} | Ewma reward: {:0.6f}".format(
                np.mean(single_run_epoch_rewards_test),
                utils.ewma(single_run_epoch_rewards_test)))
    return single_run_epoch_rewards_test


if __name__ == '__main__':
    # Data loading and build the dictionaries that use unique index for each state
    (dict_room_desc, dict_quest_desc) = framework.make_all_states_index()
    NUM_ROOM_DESC = len(dict_room_desc)
    NUM_QUESTS = len(dict_quest_desc)

    # set up the game
    framework.load_game_data()

    epoch_rewards_test = []  # shape NUM_RUNS * NUM_EPOCHS

    for _ in range(NUM_RUNS):
        epoch_rewards_test.append(run())

    epoch_rewards_test = np.array(epoch_rewards_test)

    x = np.arange(NUM_EPOCHS)
    fig, axis = plt.subplots()
    axis.plot(x, np.mean(epoch_rewards_test,
                         axis=0))  # plot reward per epoch averaged per run
    axis.set_xlabel('Epochs')
    axis.set_ylabel('reward')
    axis.set_title(('Tablular: nRuns=%d, Epilon=%.2f, Epi=%d, alpha=%.4f' %
                    (NUM_RUNS, TRAINING_EP, NUM_EPIS_TRAIN, ALPHA)))
    plt.show()

    print("Average episodic reward: " + str(epoch_rewards_test[-1]))
    print("Average episodic reward Mean: " + str(np.mean(epoch_rewards_test[-1][-20:-1])))
