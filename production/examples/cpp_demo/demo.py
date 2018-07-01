from production.examples.cpp_demo import sample


def main():  # pragma: no cover
    print('N =', sample.N)
    print(sample.square(2), sample.square(2.0))
    print(sample.reverse([1, 2, 3]))

    hz = sample.Hz()
    hz.a = 1
    hz.b = 'b'
    hz2 = sample.Hz(hz)
    hz.a = 2
    print(hz, hz2)


if __name__ == '__main__':
    main()
