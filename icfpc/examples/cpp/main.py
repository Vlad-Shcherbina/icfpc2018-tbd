from icfpc.examples.cpp import extension


def main():
    print('N =', extension.N)
    print(extension.square(2), extension.square(2.0))
    print(extension.reverse([1, 2, 3]))

    hz = extension.Hz()
    hz.a = 1
    hz.b = 'b'
    hz2 = extension.Hz(hz)
    hz.a = 2
    print(hz, hz2)


if __name__ == '__main__':
    main()

