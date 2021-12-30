# Transformer/Utilities/MultiprocessingHelper.py


# ----------------
# Module Docstring
# ----------------

"""
.. module:: MultiprocessingHelper
    :synopsis: Contains primitives and routines for process-based parallelisation using the data-parallel model.
    :platform: Unix, Windows

.. moduleauthor:: Jonathan M. Skelton

"""

# -------
# Imports
# -------

import multiprocessing;
import time;
import warnings;

try:
    # Python 2.x.

    from Queue import Empty, Full;
except ImportError:
    # Python >= 3.

    from queue import Empty, Full;

# Try to import the tqdm module.

_TQDM = False;

try:
    import tqdm;

    _TQDM = True;
except ImportError:
    pass;


# ---------
# Constants
# ---------

""" Delay for polling-based inter-process communication. """

PollDelay = 0.001;

""" Per-process number of items used to define the batch size for queue-based inter-process communication. """

QueueBatchItemsPerProcess = 250;


# ----------------
# Helper Functions
# ----------------

def CPUCount():
    """
    Return the number of CPU cores on the system.

    .. warning::
        If :func:`multiprocessing.cpu_count()` raises a `NotImplementedError` (unlikely), this wrapper issues a warning and returns a "safe" value of 1.

    Returns
    -------
    [type]
        [description]
    """

    cpuCount = 1;

    # According to the documentation, cpu_count() may raise a NotImplementedError; if this happens, issue a warning.

    try:
        cpuCount = multiprocessing.cpu_count();
    except NotImplementedError:
        warnings.warn("multiprocessing.cpu_count() is not implemented on this platform -> the CPU count will default to 1.", RuntimeWarning);

    return cpuCount;


# -------
# Classes
# -------

class Counter(object):
    """
    Implements a simple shared-memory integer counter.
    Increments and decrements are protected by a lock, and reads can optionally also be protected.
    """

    def __init__(self, initialValue = 0, readLock = True):
        """
        Class constructor.

        Parameters
        ----------
        initialValue : int, optional
            initial count, by default 0.
        readLock : bool, optional
            process-safe reads, by default True.
        """

        self._value = multiprocessing.Value('i', initialValue);

    def Current(self):
        """
        Return the current value of the counter.

        Returns
        -------
        [type]
            [description]
        """

        with self._value.get_lock():
            return self._value.value;

    def Decrement(self, amount = 1):
        """
        Decrement the counter.

        Parameters
        ----------
        amount : int, optional
            amount to subtract from the counter, by default 1.
        """

        with self._value.get_lock():
            self._value.value -= amount;

    def Increment(self, amount = 1):
        """
        Increment the counter.

        Parameters
        ----------
        amount : int, optional
            amount to add to the counter, by default 1.
        """

        with self._value.get_lock():
            self._value.value += amount;

class MapperBase(object):
    """ Base for Mapper classes to be passed to the :func:`~MultiprocessingHelper.QueueMap()` routine. """

    def Map(self, item):
        """
        Map item and return output.
        This method must be overridden by derived classes.

        Parameters
        ----------
        item : [type]
            [description]

        Raises
        ------
        NotImplementedError
            `Map()` must be overridden in a derived class.
        """

        raise NotImplementedError("Error: Map() must be overridden in a derived class.");

class FunctionMapper(MapperBase):
    """ Basic Mapper which wrapps a supplied mapping function. """

    def __init__(self, mapFunction):
        """
        Class constructor.

        Parameters
        ----------
        mapFunction : [type]
            function for mapping input to output items.
        """

        assert mapFunction is not None, "Error: mapFunction cannot be None.";

        self._mapFunction = mapFunction;

    def Map(self, item):
        """
        Map item to output using the function supplied to the constructor.

        .. note::
            - If item is a single value, it is passed to the mapping function using map_function(item); if item is a tuple, it is passed with map_function(*item).
            - For functions requiring a single tuple, wrap it in an outer tuple with e.g. ((arg1, arg2), ).

        Parameters
        ----------
        item : [type]
            [description]

        Returns
        -------
        [type]
            [description]
        """

        if isinstance(item, tuple):
            # If item is a tuple, unpack it using the *args syntax.

            return self._mapFunction(*item);
        else:
            return self._mapFunction(item);

class AccumulatorBase(object):
    """ Base for Accumulators to be passed to the :func:`~MultiprocessingHelper.QueueAccumulate()` routine. """

    def Accumulate(self, item):
        """
        Process/accumulate a new item.
        This method must be overridden in derived classes.

        Parameters
        ----------
        item : [type]
            [description]

        Raises
        ------
        NotImplementedError
            `Accumulate()` must be overridden by derived classes.
        """

        raise NotImplementedError("Error: Accumulate() must be overridden by derived classes.");

    def Finalise(self):
        """
        Finalise processing and return accumulated output.
        This method must be overridden in derived classes.

        Raises
        ------
        NotImplementedError
            `Finalise()` must be overridden by derived classes.
        """

        raise NotImplementedError("Error: Finalise() must be overridden by derived classes.");


# ------------------
# QueueMap* Routines
# ------------------

def QueueMap(inputList, mappers, progressBar = False):
    """
    Map items in inputList to an in-order list of outputs, dividing the work among the supplied set of Mapper objects.
    Each Mapper is passed to a worker process, and the input list is processed in parallel using a queue-based producer-consumer model.

    .. note::
        - There is no guarentee which `Mapper` will process which input item(s), so all Mappers must return the same result for a given input.
        - The reason for using `Mapper` objects rather than a single mapping function is so each `Mapper` can e.g. use different working directories.
        - If the flexibilty of Mappers is not needed, the :func:`~MultiprocessingHelper.QueueMapFunction()` routine presents a similar interface to the :func:`~multiprocessing.Pool.map()` function.

    .. warning::
        - If only one mapper is supplied, the input list will be mapped in serial.
        - If the :mod:`tqdm` module is not available, setting `progressBar = True` will issue a warning and a progress bar will not be displayed.

    Parameters
    ----------
    inputList : list
        list of inputs to process with the Mappers.
    mappers : [type]
        a set of user-defined Mapper objects; the number of Mappers sets the number of worker processes that will be spawned.
    progressBar : bool, optional
        if True, and if the tqdm module is available, display a progress bar during mapping, by default False.

    Returns
    -------
    [type]
        [description]

    Raises
    ------
    Exception
        [description]
    Exception
        [description]
    """


    if inputList == None:
        raise Exception("Error: inputList cannot be None.");

    if mappers == None or len(mappers) == 0:
        raise Exception("Error: At least one mapper must be supplied.");

    numInputItems = len(inputList);

    if numInputItems == 0:
        # Don't do any work if we don't have to (!).

        return [];

    # If progressBar is set but the tqdm module is not available, issue a warning and reset it.

    if progressBar and not _TQDM:
        warnings.warn("The tqdm module could not be imported -> progressBar will be reset to False.", RuntimeWarning);

        progressBar = False;

    # Create output list.

    outputList = [None for _ in range(0, numInputItems)];

    # Set up a primary iterator.
    # If the tqdm module is available, wrap the iterator to display a progress bar.

    iValues = range(0, numInputItems);

    if progressBar:
        iValues = tqdm.tqdm(iValues);

    if len(mappers) == 1:
        # If there's only one mapper, there's no point in passing all the inputs and outputs through shared-memory queues.

        mapper = mappers[0];

        for i in iValues:
            outputList[i] = mapper.Map(inputList[i]);

    else:
        # Queue for passing input items to worker processes.

        inputQueue = multiprocessing.Queue();

        # Queue for receiving input items from worker processes.

        outputQueue = multiprocessing.Queue();

        # Flag to signal worker processes to terminate.

        terminateFlag = multiprocessing.Value('B', 0);

        # Initialise worker processes.

        workerProcesses = [
            multiprocessing.Process(target = _QueueMap_ProcessMain, args = (mapper, inputQueue, outputQueue, terminateFlag))
                for mapper in mappers
            ];

        for process in workerProcesses:
            process.start();

        # Send input items to the worker threads and receive outputs.

        # The multiprocessing.Queue() has a fixed maximum size (at least on some platforms), so we need to put/get input/output items in batches.
        # If we don't, with large numbers of input items, the progress bar (if using) will not appear until the workers have processed enough items to allow the whole input list to be queued.
        # Worse still, if the output queue fills up before this can be done, we may end up with the equivalent of a deadlock.

        # Define the batch size as a fixed multiple of the number of worker processes.

        batchSize = QueueBatchItemsPerProcess * len(workerProcesses);

        # Keep track of the next item to queue.

        inputListPointer = 0;

        # Submit an initial batch of work items.

        for _ in range(0, min(batchSize, numInputItems)):
            # Just in case batchSize < numInputItems happens to exceed the maximum queue size.

            try:
                inputQueue.put_nowait(
                    (inputListPointer, inputList[inputListPointer])
                    );

                inputListPointer += 1;
            except Full:
                break;

        # Go into a queue/dequeue loop until all the outputs have been retrieved.

        for i in iValues:
            if i % batchSize == 0 or i == inputListPointer:
                # Queue more input items if required.

                for _ in range(0, min(batchSize, numInputItems - inputListPointer)):
                    try:
                        inputQueue.put_nowait(
                            (inputListPointer, inputList[inputListPointer])
                            );

                        inputListPointer += 1;
                    except Full:
                        break;

            while True:
                # Try to fetch an output item and update the output list.
                # If none are available, sleep for a delay and try again.

                try:
                    index, item = outputQueue.get_nowait();
                    outputList[index] = item;

                    break;
                except Empty:
                    time.sleep(PollDelay);

        # Set the terminate flag and wait for the worker processes to pick it up and terminate.

        terminateFlag.value = 1;

        for process in workerProcesses:
            process.join();

    # Padding after progress bar.

    if progressBar:
        print("");

    # Finally, return the output list.

    return outputList;

def QueueMapFunction(mapFunction, inputList, maxNumProcesses = CPUCount(), progressBar = True):
    """
    Map items in inputList through mapFunction and return a list of outputs.
    This routine effectively implements a queue-based alternative to :func:`~multiprocessing.Pool.map()` with support for a TQDM progress bar.

    .. note:: 
        - Internally, `mapFunction` is wrapped by :class:`~MultiprocessingHelper.FunctionMapper` classes; therefore, pasing input items to the function works as per the :func:`~MultiprocessingHelper.FunctionMapper.Map()` function of `FunctionMapper`.
        - If an item is a single value, it is passed to the mapping function with `map_function(item)`; if it is a tuple, it is passed as `map_function(*item)`.
        - Single-tuple arguments will need to be wrapped in an outer tuple, e.g. `((arg1, arg2), )`.
        - As for :func:`QueueMap()`, if `maxNumProcesses` is set to 1, a serial mapping will be performed without spawning any worker processes.

    .. warning::
        - Similarly, if the :mod:`tqdm` module is not available, setting `progressBar = True` will not work and will cause a warning to be issued.

    Parameters
    ----------
    mapFunction : [type]
        [description]
    inputList : [type]
        [description]
    maxNumProcesses : [type], optional
        maximum number of worker processes, by default MultiprocessingHelper.CPUCount().
    progressBar : bool, optional
        if True, and if the tqdm module is available, display a progress bar during mapping, by default True.

    Returns
    -------
    [type]
        [description]

    Raises
    ------
    AssertionError
        if mapFunction is None.
    """

    assert mapFunction is not None, "Error: mapFunction cannot be None.";

    # Don't spin up more processes than necessary.

    numProcesses = min(maxNumProcesses, len(inputList));

    # Wrap mapFunction in a FunctionMapper class, and call QueueMap with numProcesses copies of it.

    mapper = FunctionMapper(mapFunction);

    return QueueMap(inputList, [mapper] * numProcesses, progressBar = progressBar);

def _QueueMap_ProcessMain(mapper, inputQueue, outputQueue, terminateFlag):
    """
    Worker process function for processes spawned by the :func:`~MultiprocessingHelperQueueMap()` function.

    Parameters
    ----------
    mapper : [type]
        Mapper object to be used to map input items to outputs.
    inputQueue : [type]
        queue from which to retrieve (index, item) tuples to process.
    outputQueue : [type]
        queue in which to place (index, item) output.
    terminateFlag : [type]
        shared-memory flag used to signal the worker process to terminate.
    """

    while True:
        try:
            # Try to get an input item from the input queue and process it.

            index, inputItem = inputQueue.get_nowait();

            outputItem = mapper.Map(inputItem);

            # In this case, we do want to wait until we can put outputItem back into the queue.

            outputQueue.put(
                (index, outputItem)
                );

        except Empty:
            # Check whether the process has been signalled to terminate.
            # If not, sleep for a delay and check the input queue again.

            if terminateFlag.value == 1:
                break;

            time.sleep(PollDelay);


# -----------------------
# QueueAccumulate Routine
# -----------------------

def QueueAccumulate(inputList, accumulators, progressBar = False):
    """
    Accumulate items in inputList, dividing the work among the supplied set of Accumulator objects.
    Each Accumulator is passed to a worker process, and the input list is processed in parallel using a queue-based system.

    .. note::
        - If only one Accumulator is supplied, the input list will be processed in serial.

    .. warning::
        - As for the :func:`~MultiprocessingHelper.QueueMap()` function, setting `progressBar = True` when the :mod:`tqdm` module is not available will issue a warning, and a progress bar will not be displayed.

    Parameters
    ----------
    inputList : list
        list of inputs to process with Accumulators.
    accumulators : [type]
        a set of user-defined Accumulator objects; the number supplied sets the number of worker processes spawned.
    progressBar : bool, optional
        if True, display a progress bar during mapping (requires the `tqdm` module).

    Returns
    -------
    accumulatorResults : list
        [description]

    Raises
    ------
    AssertionError
        if inputList is None.
    Exception
        if no accumulator is supplied.
    """
    

    assert inputList is not None, "Error: inputList cannot be None.";

    assert any((accumulators is not None, len(accumulators) != 0)), "Error: inputList cannot be None.";

    # If progressBar is set but the tqdm module is not available, issue a warning and reset it.

    if progressBar and not _TQDM:
        warnings.warn("The tqdm module could not be imported -> progressBar will be reset to False.", RuntimeWarning);

        progressBar = False;

    numInputItems = len(inputList);

    # Set up a primary iterator.
    # If the tqdm module is available, wrap the iterator to display a progress bar.

    iValues = range(0, numInputItems);

    if progressBar:
        iValues = tqdm.tqdm(iValues);

    # Variable to store accumulator results.

    accumulatorResults = None;

    if len(accumulators) == 1:
        # If there's only one accumulator, there's no point in passing all the inputs and outputs through shared-memory queues.

        accumulator = accumulators[0];

        for i in iValues:
            accumulator.Accumulate(inputList[i]);

        accumulatorResults = [accumulator.Finalise()];

    else:
        # Queue for passing input items to worker processes and receving finalised results.

        inputQueue = multiprocessing.Queue();
        outputQueue = multiprocessing.Queue();

        # Shared-memory counter to keep track of the number if input items processed.

        inputCounter = Counter();

        # Flag to signal worker processes to finalise and return the results of the accumulations and terminate.

        terminateFlag = multiprocessing.Value('B', 0);

        # Initialise workers.

        workerProcesses = [
            multiprocessing.Process(target = _QueueAccumulate_ProcessMain, args = (accumulator, inputQueue, inputCounter, outputQueue, terminateFlag))
                for accumulator in accumulators
            ];

        for process in workerProcesses:
            process.start();

        # Send input items to the worker threads and monitor the progress through the shared counter.
        # Once all the input items have been accumulated, set the terminate flag and receive and return the results of the accumualations.

        # As in the QueueMap() routine, a general implementation requires input items to be queued in batches.

        batchSize = QueueBatchItemsPerProcess * len(workerProcesses);

        inputListPointer = 0;

        # Initial batch of work items.

        for _ in range(0, min(batchSize, numInputItems)):
            try:
                inputQueue.put_nowait(inputList[inputListPointer]);
                inputListPointer += 1;
            except Full:
                break;

        # Queue remaining items and monitor progress with the shared counter.

        for i in iValues:
            if i % batchSize == 0 or i == inputListPointer:
                # Queue more input items if available.

                for _ in range(0, min(batchSize, numInputItems - inputListPointer)):
                    try:
                        inputQueue.put_nowait(inputList[inputListPointer]);
                        inputListPointer += 1;
                    except Full:
                        break;

            while True:
                # Poll until the shared counter is >= i.

                if inputCounter.Current() >= i:
                    break;

                time.sleep(PollDelay);

        # Set the terminate flag and receive results from the worker processes.

        terminateFlag.value = 1;

        # get() should block until items are available, and we know how many we expect to receive -> no need to poll.

        accumulatorResults = [
            outputQueue.get()
                for _ in accumulators
            ];

        # Wait for processes to terminate.

        for process in workerProcesses:
            process.join();

    # Padding after progress bar.

    if progressBar:
        print();

    # Return results.

    return accumulatorResults;

def _QueueAccumulate_ProcessMain(accumulator, inputQueue, inputCounter, outputQueue, terminateFlag):
    """
    Worker process function for processes spawned by the :func:`~MultiprocessingHelper.QueueAccumulate()` function.

    Parameters
    ----------
    accumulator : [type]
        Accumulator object to be used to accumulate input items.
    inputQueue : [type]
        queue from which to retrieve input items to process.
    inputCounter : [type]
        shared-memory counter used to track the progress of the input processing.
    outputQueue : [type]
        queue in which to place the result returned by the `Finalise()` method of the accumulator once all input items have been processed.
    terminateFlag : [type]
        shared-memory flag used to signal the worker process to finalise the accumulation, return the result, and terminate.
    """
    while True:
        try:
            # Try to get an item from the input queue.
            # If successful, accumulate it and increment the shared counter.

            inputItem = inputQueue.get_nowait();

            accumulator.Accumulate(inputItem);

            inputCounter.Increment();

        except Empty:
            # If terminateFlag is set, call the Finalise() method on the accumulator and put the result into the output queue.
            # If not, sleep for a delay and check the input queue again.

            if terminateFlag.value == 1:
                outputQueue.put(
                    accumulator.Finalise()
                    );

                break;

            time.sleep(PollDelay);