import torch
import torch.nn as nn

class TemporalBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, dilation):
        super().__init__()
        padding = (kernel_size - 1) * dilation

        self.conv = nn.Conv1d(
            in_channels, out_channels,
            kernel_size,
            padding=padding,
            dilation=dilation
        )
        self.relu = nn.ReLU()
        self.downsample = (
            nn.Conv1d(in_channels, out_channels, 1)
            if in_channels != out_channels else None
        )

    def forward(self, x):
        out = self.conv(x)
        out = out[:, :, :-self.conv.padding[0]]  # causal
        out = self.relu(out)
        res = x if self.downsample is None else self.downsample(x)
        return out + res


class TCN(nn.Module):
    def __init__(self, input_len=12, output_len=3, channels=[32, 32, 32]):
        super().__init__()

        layers = []
        in_ch = 1
        for i, ch in enumerate(channels):
            layers.append(
                TemporalBlock(
                    in_ch, ch,
                    kernel_size=3,
                    dilation=2 ** i
                )
            )
            in_ch = ch

        self.tcn = nn.Sequential(*layers)
        self.fc = nn.Linear(channels[-1], output_len)

    def forward(self, x):
        # x: [B, T] → [B, 1, T]
        x = x.unsqueeze(1)
        h = self.tcn(x)
        h = h[:, :, -1]  # 最后一个时间步
        return self.fc(h)