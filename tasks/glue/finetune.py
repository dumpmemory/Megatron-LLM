# Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.

"""GLUE finetuning/evaluation."""

from megatron import get_args
from megatron import print_rank_0
from megatron import get_tokenizer
# from megatron.model.classification import Classification
import megatron.model.classification
from tasks.eval_utils import accuracy_func_provider
from tasks.finetune_utils import finetune
import megatron.initialize
from megatron.model.enums import ModelType


def _glue_classification(num_classes,
                         Dataset,
                         name_from_datapath_func):

    def train_valid_datasets_provider():
        """Build train and validation dataset."""
        args = get_args()
        tokenizer = get_tokenizer()

        train_dataset = Dataset('training', args.train_data,
                                tokenizer, args.seq_length)
        valid_dataset = Dataset('validation', args.valid_data,
                                tokenizer, args.seq_length)

        return train_dataset, valid_dataset

    def model_provider(pre_process=True,
                       post_process=True):
        """Build the model."""
        args = get_args()

        print_rank_0('building classification model for {} ...'.format(args.task))

        model_type_glue = ModelType.encoder_or_decoder
        model = megatron.model.classification.Classification(num_classes=num_classes,
                                                             num_tokentypes=2,
                                                             pre_process=pre_process,
                                                             post_process=post_process,
                                                             model_type=model_type_glue)
        return model

    def metrics_func_provider():
        """Privde metrics callback function."""
        def single_dataset_provider(datapath):
            args = get_args()
            tokenizer = get_tokenizer()

            name = name_from_datapath_func(datapath)
            return Dataset(name, [datapath], tokenizer, args.seq_length)
        return accuracy_func_provider(single_dataset_provider)

    """Finetune/evaluate."""
    model_type_glue = ModelType.encoder_or_decoder
    finetune(train_valid_datasets_provider,
             model_provider,
             model_type_glue,
             end_of_epoch_callback_provider=metrics_func_provider)


def main():
    megatron.initialize.initialize_megatron(extra_args_provider=None)
    # Set pytorch JIT layer fusion options and warmup JIT functions.
    # set_jit_fusion_options()

    args = get_args()

    if args.task == 'MNLI':
        num_classes = 3
        from tasks.glue.mnli import MNLIDataset as Dataset

        def name_from_datapath(datapath):
            return datapath.split('MNLI')[-1].strip(
                '.tsv').strip('/').replace('_', '-')

    elif args.task == 'QQP':

        num_classes = 2
        from tasks.glue.qqp import QQPDataset as Dataset

        def name_from_datapath(datapath):
            return datapath.split('QQP')[-1].strip(
                '.tsv').strip('/').replace('_', '-')

    else:
        raise NotImplementedError('GLUE task {} is not implemented.'.format(
            args.task))

    _glue_classification(num_classes, Dataset, name_from_datapath)


if __name__ == "__main__":
    main()
