import time
import torch
import torch.utils.data as torchdata
import numpy as np
import tqdm
import utils
import torch.nn as nn
import argparse

# ============================================================
#                    ARGUMENT PARSER
# ============================================================

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='R110_C10')
parser.add_argument('--data_dir', default='data/')
parser.add_argument('--load', default=None)
parser.add_argument('--max_batches', type=int, default=50,
                    help='Số batch test tối đa để chạy nhanh')
args = parser.parse_args()

# ============================================================
#                   FLOPs COUNTING LAYERS
# ============================================================

class FConv2d(nn.Conv2d):
    def __init__(self, *args, **kwargs):
        super(FConv2d, self).__init__(*args, **kwargs)
        self.num_ops = 0

    def forward(self, x):
        out = super().forward(x)
        output_area = out.size(-1) * out.size(-2)
        filter_area = np.prod(self.kernel_size)

        self.num_ops += (
            2 * self.in_channels * self.out_channels *
            filter_area * output_area
        )
        return out


class FLinear(nn.Linear):
    def __init__(self, *args, **kwargs):
        super(FLinear, self).__init__(*args, **kwargs)
        self.num_ops = 0

    def forward(self, x):
        out = super().forward(x)
        self.num_ops += 2 * self.in_features * self.out_features
        return out


# Replace default layers
nn.Conv2d = FConv2d
nn.Linear = FLinear


# ============================================================
#                         FLOPs COUNTER
# ============================================================

def count_flops(model, reset=True):
    total = 0
    for m in model.modules():
        if hasattr(m, 'num_ops'):
            total += m.num_ops
            if reset:
                m.num_ops = 0
    return total


# ============================================================
#                         TEST FUNCTION
# ============================================================

def run_test(model_type, model_path=None, data_dir='data/', max_batches=50):

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Dataset
    _, testset = utils.get_dataset('R110_C10', data_dir)
    testloader = torchdata.DataLoader(testset, batch_size=1,
                                      shuffle=False, num_workers=2)

    # Load model
    if model_type == 'resnet101':
        model, _ = utils.get_model('R110_C10')

    elif model_type in ['blockdrop-speed', 'blockdrop-accuracy']:
        _, model = utils.get_model('R110_C10')
        if model_path:
            utils.load_checkpoint(model, None, model_path)

    else:
        raise ValueError("Unknown model type: " + model_type)

    model.eval().to(device)

    total_flops_list = []
    matches = []
    times = []

    start_total = time.perf_counter()

    with torch.no_grad():

        for batch_idx, (inputs, targets) in tqdm.tqdm(
                enumerate(testloader), total=max_batches):

            if batch_idx >= max_batches:
                break  # Early stop

            inputs, targets = inputs.to(device), targets.to(device)

            # ------------------- Timing -------------------
            start = time.perf_counter()

            # ----------- FLOPs Before -----------
            flops_before = count_flops(model, reset=False)

            # ----------- FORWARD (no agent policy) -----------
            if hasattr(model, "layer_config"):
                # FlatResNet / BlockDrop requires (batch, num_blocks)
                num_blocks = sum(model.layer_config)
                policy = torch.ones((inputs.size(0), num_blocks)).to(device)
                preds = model(inputs, policy)
            else:
                preds = model(inputs)

            # ----------- FLOPs After -----------
            flops_after = count_flops(model, reset=False)
            total_flops_list.append(flops_after - flops_before)

            # ------------------- Time per image -------------------
            end = time.perf_counter()
            times.append((end - start) * 1000)  # ms

            # ------------------- Accuracy -------------------
            _, pred_idx = preds.max(1)
            matches.append((pred_idx == targets).float().item())

    # ============================================================
    #                     FINAL METRICS
    # ============================================================

    total_time = time.perf_counter() - start_total

    avg_acc = np.mean(matches)
    avg_flops = np.mean(total_flops_list)
    std_flops = np.std(total_flops_list)
    avg_time = np.mean(times)

    # ============================================================
    #                     LOGGING (Research Style)
    # ============================================================

    print("\n====================================================")
    print(f"                TEST RESULTS: {model_type}         ")
    print("====================================================")
    print(f" Tested Samples        : {len(matches)}")
    print(f" Accuracy (%)          : {avg_acc * 100:.2f}")
    print(f" FLOPs/img (avg)       : {avg_flops:.2e}")
    print(f" FLOPs/img (std)       : {std_flops:.2e}")
    print(f" Time per image (ms)   : {avg_time:.3f}")
    print(f" Total runtime (s)     : {total_time:.2f}")
    print("====================================================\n")


# ============================================================
#                           MAIN
# ============================================================

if __name__ == "__main__":
    data_dir = args.data_dir
    max_batches = args.max_batches

    print("\n==== Testing ResNet101 Baseline ====")
    run_test('resnet101', data_dir=data_dir, max_batches=max_batches)

    # print("\n==== Testing BlockDrop - Speed Priority ====")
    # run_test('blockdrop-speed', model_path='checkpoint_speed.pt',
    #          data_dir=data_dir, max_batches=max_batches)

    # print("\n==== Testing BlockDrop - Accuracy Priority ====")
    # run_test('blockdrop-accuracy', model_path='checkpoint_acc.pt',
    #          data_dir=data_dir, max_batches=max_batches)
