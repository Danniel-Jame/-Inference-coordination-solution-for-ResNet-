import time
import torch
import torch.utils.data as torchdata
import numpy as np
import tqdm
import utils
import torch.nn as nn
import numpy as np

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--model', default='R110_C10')
parser.add_argument('--data_dir', default='data/')
parser.add_argument('--load', default=None)
args = parser.parse_args()

class FConv2d(nn.Conv2d):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1,
                 padding=0, dilation=1, groups=1, bias=True):
        super(FConv2d, self).__init__(in_channels, out_channels, kernel_size, stride,
                                      padding, dilation, groups, bias)
        self.num_ops = 0

    def forward(self, x):
        output = super(FConv2d, self).forward(x)
        output_area = output.size(-1)*output.size(-2)
        filter_area = np.prod(self.kernel_size)
        self.num_ops += 2*self.in_channels*self.out_channels*filter_area*output_area
        return output


class FLinear(nn.Linear):
    def __init__(self, in_features, out_features, bias=True):
        super(FLinear, self).__init__(in_features, out_features, bias)
        self.num_ops = 0

    def forward(self, x):
        output = super(FLinear, self).forward(x)
        self.num_ops += 2*self.in_features*self.out_features
        return output


# Thay thế lớp mặc định của PyTorch bằng lớp đếm FLOPs
nn.Conv2d = FConv2d
nn.Linear = FLinear


def count_flops(model, reset=True):
    op_count = 0
    for m in model.modules():
        if hasattr(m, 'num_ops'):
            op_count += m.num_ops
            if reset:
                m.num_ops = 0
    return op_count

rnet, agent = utils.get_model(args.model)

def run_test(model_type, model_path=None, target_accuracy=None, data_dir='data/'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    testset = utils.get_dataset('R110_C10', data_dir)[1]
    testloader = torchdata.DataLoader(testset, batch_size=1, shuffle=False, num_workers=2)
    
    total_ops = []
    matches, policies = [], []
    for batch_idx, (inputs, targets) in tqdm.tqdm(enumerate(testloader), total=len(testloader)):

        device = torch.device("cpu")
        with torch.no_grad():
             inputs, targets = inputs.to(device), targets.to(device)
        probs, _ = agent(inputs)

        policy = probs.clone()
        policy[policy<0.5] = 0.0
        policy[policy>=0.5] = 1.0

        preds = rnet.forward_single(inputs, policy.data.squeeze(0))
        _ , pred_idx = preds.max(1)
        match = (pred_idx==targets).data.float()

        matches.append(match)
        policies.append(policy.data)

        ops = count_flops(agent) + count_flops(rnet)
        total_ops.append(ops)

    if model_type == 'resnet101':
        model, _ = utils.get_model('R110_C10')  # cần có nhánh phù hợp trong utils.py
        model.eval().to(device)

    elif model_type == 'blockdrop-speed':
        _, model = utils.get_model('R110_C10')
        if model_path:
            utils.load_checkpoint(model, None, model_path)
        model.eval().to(device)

    elif model_type == 'blockdrop-accuracy':
        _, model = utils.get_model('R110_C10')
        if model_path:
            utils.load_checkpoint(model, None, model_path)
        model.eval().to(device)

    else:
        raise ValueError("Unknown model type")


    start_time = time.perf_counter()
    total_flops = 0
    matches = []

    with torch.no_grad():
        for inputs, targets in tqdm.tqdm(testloader):
            inputs, targets = inputs.to(device), targets.to(device)
            total_flops += count_flops(model, reset=False)

            if 'blockdrop' in model_type:
                # BlockDrop model requires policy argument for forward()
                if hasattr(model, 'forward_single'):
                    preds = model.forward_single(inputs)
                else:
                    num_blocks = sum(model.layer_config)
                    policy = torch.ones(num_blocks).to(device)
                    preds = model.forward(inputs, policy)
            else:
                preds = model(inputs)

            _, pred_idx = preds.max(1)
            match = (pred_idx == targets).cpu().float()
            matches.append(match)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    num_samples = len(testloader)
    avg_time_per_img = (total_time / num_samples) * 1000  # ms

    accuracy = np.mean([m.item() for m in matches])
    avg_flops = total_flops / num_samples

    print(f"Model: {model_type}")
    print(f"Avg FLOPs per image: {avg_flops:.2e}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Time per image: {avg_time_per_img:.2f} ms")


if __name__ == "__main__":
    data_dir = 'data/'

    print("\n==== Testing ResNet101 Baseline ====")
    run_test('resnet101', data_dir=data_dir)

    # print("\n==== Testing BlockDrop - Speed Priority ====")
    # run_test('blockdrop-speed', model_path='checkpoint_speed.pt', data_dir=data_dir)

    # print("\n==== Testing BlockDrop - Accuracy Priority ====")
    # run_test('blockdrop-accuracy', model_path='checkpoint_acc.pt', data_dir=data_dir)
