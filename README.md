Computer Science Bachelor's Degree Thesis project @ Unipi (2022).

# What is this project about?
This thesis project consists in the implementation of a simple application
of `Continual Learning As A Service`, and in particular in building a REST
API on top of the Continual Learning library [`Avalanche`](https://github.com/ContinualAI/avalanche)
and in deploying it using a Docker container on Unipi Servers for usage as a `Software
As A Service` application for experimenting with Continual Learning.

The REST API exposes several common Computer Vision benchmarks (e.g. SplitMNIST, SplitFashionMNIST, CoRE50,
SplitCIFAR10, SplitCIFAR100) together with the possibility of building custom benchmarks by specifying
how to subdivide the dataset in different experiences.

## What is Continual Learning?
According to the definition in [`ContinualAI Wiki Page`](https://wiki.continualai.org/):
```
A Continual learning system can be defined as an adaptive algorithm
capable of learning from a continuous stream of information, with such
information becoming progressively available over time and where the
number of tasks to be learned (e.g. membership classes in a classification
task) are not predefined. Critically, the accommodation of new information
should occur without catastrophic forgetting or interference.
Parisi et al. Continual Lifelong Learning with Neural Networks: a review, 2019.
```

Continual Learning is hence a research branch in the field of AI whose aim is to study
learning strategies to allow AI agents to learn in a context in which it is required to
be capable to *autonomously* learn new skills or to extend previous (e.g. classification)
capabilities *without* having to be retrained from scratch each time. In CL terminology,
we say that the agent passes through a series of **experiences**, and in each one it acquires
new data corresponding to new tasks to learn or to extension/modifications of previous tasks
(e.g. for a shift in the distribution underlying the problem at end).

A `Continual Learning As A Service` system is similar to a `Machine Learning As A Service` system,
with the difference that we make use of Continual Learning Strategies, monitoring and Continuous
updates of the models.

# What I have implemented
My implementation is a *Proof-of-Concept* for showing how a CLaaS system may
be *actually* implemented as a SaaS service for a real cloud service in a production
context. I have tried to implement something as scalable and implementation-independent
as possible to simplify as much as possible the transition to a MongoDB cluster for database
management, a cloud storage service provider for storing user data and models, and Kubernetes
for container orchestration in order to have multiple running instances of the application, and
possibly to extend the system to a `PaaS` one by handling user code in sandboxed containers.

### Users, Workspaces, Data Repositories
I have designed the application to provide:
* User registration and login through the `Bearer Token` protocol (tokens with expiration);
* each User has one or more `Workspaces` that can be used for storing data and experiments
configurations and possibly for sharing them between different users;
* each Workspace has one or more associated *`Data Repositories`* - virtual filesystems for
storing datasets for custom experiments (for instance, one can use folders and subfolders to impose a structure
on which files to use for each experience).

### Benchmarks and Datasets
`Benchmarks` are couples `(Dataset, Scenario)` which describe how to partition the dataset according e.g.
to a *task-incremental* or a *domain-incremental* scenario etc. There are several "standard" (i.e., already
provided in Avalanche) benchmarks that can be used for simple experiments. Aside from that, I
provided the possibility to upload data in `.zip` format to make custom dataset and benchmarks.

Available standard benchmarks are:
* SplitMNIST
* SplitFashionMNIST
* RotatedMNIST
* PermutedMNIST
* SplitCIFAR10
* SplitCIFAR100
* CORe50
* SplitTinyImageNet

### Models
Most classic Machine Learning models can be used in a Continual Learning environment since *Strategies*
will describe how to train at each experience. However, some CL-related are MultiTask / MultiHead models,
in which each head is dedicated to one single task. Available models are:
* classic MLPs
* simple CNNs (see Avalanche doc)
* MultiHead MLP
* Progressive Neural Networks
* Small VGG
* MultiHead VGG
* MultiHead Small VGG
* `torchvision` models like `GoogLeNet`, `AlexNet`, `MobileNet` etc

### Available Strategies
`Strategies` define how to train and adapt a Continual Learning model through the experiences.
For instance:
* `Naive` strategy consists in training the model `only` on the newly available data, but it incurs in
the `Catastrophic Forgetting` phenomenon;
* `Cumulative` strategy consists in training each time the model *from scratch*, giving the best results
in accuracy scores but being unfeasible in contexts like real-time robotics etc.
* `Replay` strategy consists in using a buffer that hosts a portion of examples from previous
experiences to be used when training for the current one. Depending on the size of the buffer,
this can give a significant speedup (4-5 times faster) w.r.t. `Cumulative` strategy, but it may
not reach the *same* accuracy scores

All three strategies are available, together with:
* Joint Training
* GDumb strategies
* SynapticIntelligence
* Elastic Weight Consolidation (EWC)
* Learning without Forgetting (LwF)
* CWRStar
* AGEM

### Metrics
A Continual Learning models may be monitored by its scores on several metrics. Apart from
accuracy/loss, in CL there is a focus also on:
* forgetting
* timing
* RAM usage
* CPU usage
* GPU usage
* Backward Transfer
* Forward Transfer
* MAC

### Deployment and Inference
After having performed your experiments, the final model(s) may be *deployed*
*directly* on the platform, by giving to each one a specific URL built for instance
on top of its location in the internal server filesystem. Deployed models may be used
to perform *online inference* like in a MLaaS system.

## Tools
* `Flask` for the backend (handling requests etc.)
* `Avalanche` for Continual Learning (standard) Benchmarks, Models, Strategies, Criterions and Metrics
* `PyTorch` as base framework for Avalanche and for providing common Computer Vision pretrained models
(e.g. `GoogLeNet`, `MobileNet`, `AlexNet` etc.)
* `MongoDB` as database for storing users data and information along with Benchmarks, Models, Strategies,
Criterions, Metrics and Experiments configurations and results
* `Docker` and `Docker Compose` for containerization and handling the execution of `main` service
and `MongoDB` (serialization over an external volume)
* `Postman` for testing the API
* For maintaining the data produced by the experiments and the trained models to deploy I have used
local filesystem, but the interface is realized for allowing implementation with `Amazon S3` or other
cloud storage services providers.

## Resources and Credits
* [`ContinualAI`](https://www.continualai.org/) website - a non-profit organization whose aim is, as they say:
*to create an open-source, collaborative wiki to provide a starting point for researchers, developers and AI enthusiasts who share an interest in Continual Learning and are willing to learn more or contribute to this field*;
* [`Avalanche`](https://github.com/ContinualAI/avalanche) GitHub Repository.

* Thanks to professor [`Vincenzo Lomonaco`](https://www.linkedin.com/in/vincenzolomonaco/), founder of ContinualAI, for the possibility of working
on such an interesting project on this field, both from a theoretical and a practical point of view.

* Thanks to [`Rudy Semola`](https://www.linkedin.com/in/rudysemola/), PhD student at the University of Pisa, for help and suggestions in studying Continual
Learning and in how to approach the problem of a `Continual Learning As A Service` system.