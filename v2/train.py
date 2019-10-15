import time
import sys
import snflow as flow
import plac
import tensorflow as tf
import segmentation_models as sm
import keras
import numpy as np
import logging
logger = logging.getLogger(__name__)

callbacks = [
    keras.callbacks.ModelCheckpoint('./best_model.h5', save_weights_only=True, save_best_only=True, mode='min'),
    keras.callbacks.ReduceLROnPlateau(),
]

dice_loss = sm.losses.DiceLoss(class_weights=np.array([0.2, 1, 1, 1]))
focal_loss = sm.losses.BinaryFocalLoss() if flow.N_CLASSES == 1 else sm.losses.CategoricalFocalLoss()
total_loss = dice_loss + (1 * focal_loss)
metrics = ['accuracy', sm.metrics.IOUScore(threshold=0.5), sm.metrics.FScore(threshold=0.5)]
optim = keras.optimizers.Adam()

def save_model(model, save_path="model.hdf5", pause=0):
    if pause > 0:
        sys.stderr.write("Saving in")
        for i in list(range(1,6))[::-1]:
            sys.stderr.write(" %d...\n" % i)
            time.sleep(pause)
    sys.stderr.write("Saving...\n")
    return model.save_weights(save_path)

def main(save_path="model.hdf5",
         optimizer='adam',
         loss='sparse_categorical_crossentropy',
         restore=True,
         verbose=1,
         epochs=20,
         validation_split=0.1):
    model = sm.Unet(flow.BACKBONE, classes=flow.N_CLASSES, activation='softmax')

    if restore:
        try:
            model.load_weights(save_path)
            logger.info("Model loaded successfully.")
        except OSError as exc:
            sys.stderr.write(str(exc) + "\n")

    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
#    model.summary()

    seq = flow.Sequence()
    while True:
        try:
            for x,y in seq:
                model.fit(x, y, batch_size=seq.batch_size,
                          validation_split=validation_split,
                          epochs=epochs, verbose=verbose)
        except KeyboardInterrupt:
                save_model(model, save_path, pause=1)
                sys.exit()
        except Exception as exc:
            save_model(model, save_path)
            raise(exc)

if __name__ == "__main__":
    plac.call(main)
